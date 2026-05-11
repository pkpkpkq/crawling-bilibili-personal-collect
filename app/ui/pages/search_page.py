import webbrowser
from typing import Any, Literal

from PySide6.QtCore import QModelIndex, QRect, Qt
from PySide6.QtGui import QColor, QFont, QPen
from PySide6.QtWidgets import QStyle, QVBoxLayout, QWidget

from app.models import (
    GlobalSearchFilterProxyModel,
    GlobalSearchRowRole,
    GlobalSearchRowsModel,
    PagedProxyModel,
)
from app.services.cache_service import CacheService
from app.theme import BorderRadius, Color, Spacing, Typography
from app.ui import strings
from app.ui.components.card_delegate import BaseCardDelegate
from app.ui.strings import (
    COLLECTION_CARD_BADGE_INVALID,
    COLLECTION_CARD_BADGE_UNFAVORITED,
    SEARCH_SUBTITLE_FORMAT,
    SEARCH_UP_LINK_FORMAT,
)
from app.ui.components.card_list_view import CardListView
from app.ui.components.empty_state import EmptyState
from app.ui.components.filter_bar import FilterBar
from app.ui.components.page_header import PageHeader
from app.ui.components.pagination_bar import PaginationBar


LinkTarget = Literal["bv", "up"]


class SearchVideoCardDelegate(BaseCardDelegate):
    """Warm card delegate for global-search video rows."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._up_link_rect: dict[object, QRect] = {}

    def _title_text(self, index: QModelIndex) -> str:
        return str(index.data(int(GlobalSearchRowRole.TITLE)) or "")

    def _subtitle_text(self, index: QModelIndex) -> str:
        bv_id = index.data(int(GlobalSearchRowRole.BV_ID)) or "N/A"
        up_name = index.data(int(GlobalSearchRowRole.UP_NAME)) or "N/A"
        collection = index.data(int(GlobalSearchRowRole.LATEST_COLLECTION)) or "N/A"
        fav_time = index.data(int(GlobalSearchRowRole.LATEST_FAV_TIME)) or "N/A"
        return SEARCH_SUBTITLE_FORMAT.format(bv_id=bv_id, up_name=up_name, collection=collection, fav_time=fav_time)

    def _link_text(self, index: QModelIndex) -> str:
        return str(index.data(int(GlobalSearchRowRole.BV_ID)) or "")

    def hitTestLink(self, position, index: QModelIndex) -> LinkTarget | None: # noqa: N802
        key = self._index_key(index)
        if self._link_rect.get(key, QRect()).contains(position):
            return "bv"
        if self._up_link_rect.get(key, QRect()).contains(position):
            return "up"
        return None

    def _title_color(self, option):
        index = self._paint_index
        is_invalid = bool(index.data(int(GlobalSearchRowRole.IS_INVALID)))
        is_unfavorited = bool(index.data(int(GlobalSearchRowRole.IS_UNFAVORITED)))
        is_hover = bool(option.state & QStyle.StateFlag.State_MouseOver)
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        if is_invalid or is_unfavorited:
            return Color.CHARCOAL_WARM.value
        if is_hover or is_selected:
            return Color.TERRACOTTA_BRAND.value
        return Color.ANTHROPIC_NEAR_BLACK.value

    def _configure_title_font(self, font, option, index):
        is_invalid = bool(index.data(int(GlobalSearchRowRole.IS_INVALID)))
        font.setStrikeOut(is_invalid)

    def _paint_extras(self, painter, option, index, content_rect, text_rect, y):
        key = self._index_key(index)
        is_invalid = bool(index.data(int(GlobalSearchRowRole.IS_INVALID)))
        is_unfavorited = bool(index.data(int(GlobalSearchRowRole.IS_UNFAVORITED)))

        badge_x = text_rect.right()
        badge_font = QFont(option.font)
        badge_font.setPixelSize(Typography.SIZE_LABEL)
        badge_font.setWeight(QFont.Weight.Medium)
        painter.setFont(badge_font)
        for label, color in (
            (COLLECTION_CARD_BADGE_INVALID, Color.ERROR_CRIMSON),
            (COLLECTION_CARD_BADGE_UNFAVORITED, Color.CHARCOAL_WARM),
        ):
            if (label == COLLECTION_CARD_BADGE_INVALID and not is_invalid) or (
                label == COLLECTION_CARD_BADGE_UNFAVORITED and not is_unfavorited
            ):
                continue
            metrics = painter.fontMetrics()
            badge_width = metrics.horizontalAdvance(label) + Spacing.SCALE_16
            badge_rect = QRect(
                badge_x - badge_width,
                self._title_y,
                badge_width,
                self._title_height,
            )
            painter.setPen(QPen(QColor(color.value), 1))
            painter.drawRoundedRect(badge_rect, BorderRadius.SUBTLE, BorderRadius.SUBTLE)
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, label)
            badge_x -= badge_width + Spacing.SCALE_8

        up_name = str(index.data(int(GlobalSearchRowRole.UP_NAME)) or "")
        up_id = index.data(int(GlobalSearchRowRole.UP_ID))
        bv_rect = self._link_rect.get(key)
        if up_name and up_id and bv_rect:
            up_text = SEARCH_UP_LINK_FORMAT.format(up_name=up_name)
            link_font = QFont(self._body_font)
            link_font.setWeight(QFont.Weight.Medium)
            painter.setFont(link_font)
            painter.setPen(QColor(Color.DARK_WARM.value))
            metrics = painter.fontMetrics()
            up_x = bv_rect.right() + Spacing.SCALE_20
            up_width = metrics.horizontalAdvance(up_text)
            up_rect = QRect(up_x, bv_rect.top(), up_width, bv_rect.height())
            self._up_link_rect[key] = up_rect
            painter.drawText(
                up_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, up_text
            )
            # Terracotta rgba(201,100,66,100) ≈40% opacity
            up_underline_y = up_rect.bottom() + 2
            up_underline_pen = QPen(QColor(201, 100, 66, 100), 1)
            painter.setPen(up_underline_pen)
            painter.drawLine(up_rect.left(), up_underline_y, up_rect.right(), up_underline_y)
        else:
            self._up_link_rect.pop(key, None)

        return y


class SearchPage(QWidget):
    def __init__(self, cache_service: CacheService, parent=None):
        super().__init__(parent)
        self.cache_service = cache_service

        self.source_model = GlobalSearchRowsModel()
        self.filter_proxy = GlobalSearchFilterProxyModel()
        self.filter_proxy.setSourceModel(self.source_model)

        self.paged_proxy = PagedProxyModel(page_size=50)
        self.paged_proxy.setSourceModel(self.filter_proxy)

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

        self.header = PageHeader(strings.PAGE_TITLE_GLOBAL_SEARCH)
        self.title_label = self.header.title_label
        layout.addWidget(self.header)

        sort_options = [
            strings.SORT_LATEST_FAV_DESC,
            strings.SORT_LATEST_FAV_ASC,
            strings.SORT_SEARCH_PLAY_DESC,
            strings.SORT_SEARCH_COLLECT_DESC,
        ]
        sort_keys = ["fav_desc", "fav_asc", "play_desc", "collect_desc"]
        self.filter_bar = FilterBar(sort_items=sort_options)
        self.search_input = self.filter_bar.search_input
        self.search_input.setClearButtonEnabled(True)
        self.sort_combo = self.filter_bar.sort_combo
        for i, key in enumerate(sort_keys):
            self.sort_combo.setItemData(i, key)
        layout.addWidget(self.filter_bar)

        self.list_view = CardListView()
        self.list_view.setEditTriggers(CardListView.EditTrigger.NoEditTriggers)
        self.list_view.setMouseTracking(True)
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.delegate = SearchVideoCardDelegate(self.list_view)
        self.list_view.setItemDelegate(self.delegate)

        self.pagination_bar = PaginationBar()
        self.list_view.bind_paged_proxy(self.paged_proxy, self.pagination_bar)

        self.empty_state = EmptyState(strings.EMPTY_NO_DATA)
        self.empty_state.hide()

        layout.addWidget(self.list_view, stretch=1)
        layout.addWidget(self.empty_state, stretch=1)
        layout.addSpacing(Spacing.SCALE_8)
        layout.addWidget(self.pagination_bar)
        self._update_empty_state()

    def _connect_signals(self) -> None:
        self.search_input.textChanged.connect(self.filter_proxy.setSearchText)
        self.search_input.textChanged.connect(self._update_after_filter_change)
        if self.sort_combo is not None:
            self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)

        self.filter_proxy.layoutChanged.connect(self._update_empty_state)
        self.filter_proxy.rowsInserted.connect(self._update_empty_state)
        self.filter_proxy.rowsRemoved.connect(self._update_empty_state)
        self.filter_proxy.modelReset.connect(self._update_empty_state)
        self.paged_proxy.layoutChanged.connect(self._update_empty_state)
        self.paged_proxy.modelReset.connect(self._update_empty_state)
        self.list_view.clicked.connect(self._on_list_clicked)

    def load_data(self, rows: list[dict[str, Any]]) -> None:
        self.source_model.set_rows(rows)
        self._update_empty_state()

    def set_search_text(self, text: str) -> None:
        """Programmatically set the search input text (e.g. from UP list handoff)."""
        self.search_input.setText(text)

    def _on_sort_changed(self, index: int) -> None:
        sort_key = self.sort_combo.itemData(index) or "fav_desc"
        self.filter_proxy.setSortKey(sort_key)
        self._update_empty_state()

    def _update_after_filter_change(self) -> None:
        self.paged_proxy.setCurrentPage(1)
        self._update_empty_state()

    def _update_empty_state(self) -> None:
        has_rows = self.paged_proxy.rowCount() > 0
        self.list_view.setVisible(has_rows)
        self.empty_state.setVisible(not has_rows)
        self.pagination_bar.update(
            current=self.paged_proxy.currentPage(),
            total_pages=self.paged_proxy.pageCount(),
            total_items=self.paged_proxy.totalRowCount(),
        )

    def _on_list_clicked(self, index: QModelIndex) -> None:
        if not index.isValid():
            return

        position = self.list_view.viewport().mapFromGlobal(self.list_view.cursor().pos())
        target = self.delegate.hitTestLink(position, index)

        if target == "bv":
            bv_id = index.data(int(GlobalSearchRowRole.BV_ID))
            if bv_id:
                webbrowser.open(f"https://www.bilibili.com/video/{bv_id}")
            return

        if target == "up":
            up_id = index.data(int(GlobalSearchRowRole.UP_ID))
            if up_id:
                webbrowser.open(f"https://space.bilibili.com/{up_id}")
            return
