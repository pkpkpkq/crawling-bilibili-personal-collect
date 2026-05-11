import webbrowser

from PySide6.QtCore import QModelIndex, QSize, Signal, Slot
from PySide6.QtWidgets import QVBoxLayout, QWidget

from app.models import UpListFilterProxyModel, UpListRowRole, UpListRowsModel
from app.repositories.connection import get_connection
from app.repositories.following import get_all_following_ups
from app.theme import Color, Spacing
from app.ui.components.card_delegate import BaseCardDelegate
from app.ui.components.card_list_view import CardListView
from app.ui.components.empty_state import EmptyState
from app.ui.components.filter_bar import FilterBar
from app.ui.components.page_header import PageHeader
from app.ui.strings import EMPTY_NO_DATA, PAGE_TITLE_FOLLOWING_UP, PLACEHOLDER_SEARCH_UP, UP_CARD_LINK_TEXT


class UpCardDelegate(BaseCardDelegate):
    """Warm card delegate for UP list rows."""

    def _title_text(self, index: QModelIndex) -> str:
        return str(index.data(int(UpListRowRole.NAME)) or "")

    def _subtitle_text(self, index: QModelIndex) -> str:
        mid = index.data(int(UpListRowRole.MID))
        return f"UID: {mid}" if mid is not None else ""

    def _link_text(self, index: QModelIndex) -> str:
        return UP_CARD_LINK_TEXT

    def sizeHint(self, option, index):
        return QSize(280, 100)

    def _title_color(self, option):
        from PySide6.QtWidgets import QStyle
        is_hover = bool(option.state & QStyle.StateFlag.State_MouseOver)
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        if is_hover or is_selected:
            return Color.TERRACOTTA_BRAND.value
        return Color.DARK_WARM.value


class UpListPage(QWidget):
    search_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.source_model = UpListRowsModel()
        self.filter_proxy = UpListFilterProxyModel()
        self.filter_proxy.setSourceModel(self.source_model)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            Spacing.PAGE_MARGIN,
            Spacing.PAGE_MARGIN,
            Spacing.PAGE_MARGIN,
            Spacing.PAGE_MARGIN,
        )
        layout.setSpacing(Spacing.SCALE_16)

        header = PageHeader(PAGE_TITLE_FOLLOWING_UP)
        layout.addWidget(header)

        self.filter_bar = FilterBar(sort_items=None)
        self.filter_bar.search_input.setPlaceholderText(PLACEHOLDER_SEARCH_UP)
        self.filter_bar.search_input.setClearButtonEnabled(True)
        layout.addWidget(self.filter_bar)

        self.list_view = CardListView()
        self.list_view.setModel(self.filter_proxy)
        self.delegate = UpCardDelegate(self.list_view)
        self.list_view.setItemDelegate(self.delegate)
        # Grid layout for UP cards
        self.list_view.setViewMode(CardListView.ViewMode.IconMode)
        self.list_view.setIconSize(QSize(280, 0))
        self.list_view.setGridSize(QSize(300, 120))
        self.list_view.setWrapping(True)
        self.list_view.setResizeMode(CardListView.ResizeMode.Adjust)
        self.list_view.setEditTriggers(
            CardListView.EditTrigger.NoEditTriggers
        )
        self.list_view.setMouseTracking(True)

        layout.addWidget(self.list_view, stretch=1)

        self.empty_state = EmptyState(EMPTY_NO_DATA)
        self.empty_state.hide()
        layout.addWidget(self.empty_state)
        self._update_empty_state()

    def _connect_signals(self) -> None:
        self.filter_bar.search_input.textChanged.connect(self.filter_proxy.setSearchText)
        self.filter_bar.search_input.textChanged.connect(self._update_empty_state)
        self.list_view.clicked.connect(self._on_list_clicked)

    @property
    def search_input(self):
        return self.filter_bar.search_input

    def _update_empty_state(self) -> None:
        has_rows = self.filter_proxy.rowCount() > 0
        self.list_view.setVisible(has_rows)
        self.empty_state.setVisible(not has_rows)

    def load_data(self) -> None:
        with get_connection() as conn:
            rows = get_all_following_ups(conn)
            self.source_model.set_rows(rows)
            self._update_empty_state()

    @Slot(QModelIndex)
    def _on_list_clicked(self, index: QModelIndex) -> None:
        pos = self.list_view.viewport().mapFromGlobal(
            self.list_view.cursor().pos()
        )
        if self.delegate.hitTestLink(pos, index):
            mid = index.data(int(UpListRowRole.MID))
            if mid:
                webbrowser.open(f"https://space.bilibili.com/{mid}")
            return

        up_name = self.filter_proxy.data(index, int(UpListRowRole.NAME))
        if up_name:
            self.search_requested.emit(up_name)
