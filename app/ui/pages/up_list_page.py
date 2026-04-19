import webbrowser

from PySide6.QtCore import QEvent, QModelIndex, QRect, Qt, Signal, Slot
from PySide6.QtGui import QMouseEvent, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QLineEdit,
    QListView,
    QStyledItemDelegate,
    QVBoxLayout,
    QWidget,
)

from app.models import UpListFilterProxyModel, UpListRowRole, UpListRowsModel
from app.repositories.connection import get_connection
from app.repositories.following import get_all_following_ups
from app.theme import Color, Spacing, Typography


class UpListRowDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.link_rects = {}

    def paint(self, painter: QPainter, option, index):
        painter.save()

        if option.state & QStyledItemDelegate.StateFlag.State_Selected:
            painter.fillRect(option.rect, Color.WARM_SAND.value)
        elif option.state & QStyledItemDelegate.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, Color.IVORY.value)
        else:
            painter.fillRect(option.rect, Color.PARCHMENT.value)

        up_name = index.data(int(UpListRowRole.NAME))
        mid = index.data(int(UpListRowRole.MID))

        margin = Spacing.SCALE_12
        text_rect = option.rect.adjusted(margin, margin, -margin, -margin)

        font = painter.font()
        font.setPointSize(Typography.SIZE_BODY_LARGE)
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(Color.FOCUS_BLUE.value)

        name_rect = painter.boundingRect(
            text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, up_name
        )
        painter.drawText(
            name_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, up_name
        )
        self.link_rects[index] = name_rect

        font.setPointSize(Typography.SIZE_BODY_STANDARD)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(Color.CHARCOAL_WARM.value)

        mid_rect = option.rect.adjusted(
            margin, name_rect.bottom() + Spacing.SCALE_6, -margin, -margin
        )
        painter.drawText(
            mid_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            f"MID: {mid}",
        )

        painter.restore()

    def sizeHint(self, option, index):
        return (
            super()
            .sizeHint(option, index)
            .expandedTo(option.rect.size())
            .expandedTo(QRect(0, 0, 0, 80).size())
        )

    def editorEvent(self, event, model, option, index):
        if event.type() == QEvent.Type.MouseButtonRelease:
            mouse_event: QMouseEvent = event
            if mouse_event.button() == Qt.MouseButton.LeftButton:
                link_rect = self.link_rects.get(index)
                if link_rect and link_rect.contains(mouse_event.position().toPoint()):
                    mid = index.data(int(UpListRowRole.MID))
                    if mid:
                        webbrowser.open(f"https://space.bilibili.com/{mid}")
                    return True
        return super().editorEvent(event, model, option, index)


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
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
        )
        layout.setSpacing(Spacing.SCALE_16)

        header_label = QLabel("Followed UPs")
        header_label.setObjectName("h1")
        layout.addWidget(header_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter by UP name...")
        self.search_input.setClearButtonEnabled(True)
        layout.addWidget(self.search_input)

        self.list_view = QListView()
        self.list_view.setModel(self.filter_proxy)
        self.delegate = UpListRowDelegate(self.list_view)
        self.list_view.setItemDelegate(self.delegate)
        self.list_view.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.list_view.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.list_view.setAlternatingRowColors(True)
        self.list_view.setMouseTracking(True)

        layout.addWidget(self.list_view, stretch=1)

    def _connect_signals(self) -> None:
        self.search_input.textChanged.connect(self.filter_proxy.setSearchText)
        self.list_view.clicked.connect(self._on_list_clicked)

    def load_data(self) -> None:
        with get_connection() as conn:
            rows = get_all_following_ups(conn)
        self.source_model.set_rows(rows)

    @Slot(QModelIndex)
    def _on_list_clicked(self, index: QModelIndex) -> None:
        up_name = self.filter_proxy.data(index, int(UpListRowRole.NAME))
        if up_name:
            self.search_requested.emit(up_name)
