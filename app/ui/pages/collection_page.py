import webbrowser
from typing import Any

from PySide6.QtCore import QModelIndex, QRect, QSize, Qt, QEvent, Signal, Slot
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPixmap, QPolygon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCalendarWidget,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QStackedWidget,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QVBoxLayout,
    QWidget,
)

from app.models import (
    CollectionFilterProxyModel,
    CollectionRowRole,
    CollectionRowsModel,
    PagedProxyModel,
)
from app.services.cache_service import CacheService
from app.theme import BorderRadius, Color, Spacing, Typography, get_base_stylesheet
from app.ui import strings
from app.ui.components.card_delegate import BaseCardDelegate
from app.ui.components.card_list_view import CardListView
from app.ui.components.empty_state import EmptyState
from app.ui.components.filter_bar import FilterBar
from app.ui.components.page_header import PageHeader
from app.ui.components.pagination_bar import PaginationBar
def _history_text(item: dict[str, Any]) -> str:
    action = item.get("action", item.get("type", ""))
    time = item.get("time", "")
    collection = item.get("collection_name", item.get("collection", ""))
    action_text = (
        strings.HISTORY_ACTION_ADD
        if action in {"add", "added"}
        else strings.HISTORY_ACTION_REMOVE
    )
    return f"[{time}] {action_text} | {strings.HISTORY_COLLECTION_LABEL}: {collection}"


class CollectionVideoCardDelegate(BaseCardDelegate):
    """Warm card delegate for collection videos with thumbnails and history."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cover_width = 120
        self.cover_height = 75

    def _title_text(self, index: QModelIndex) -> str:
        return str(index.data(int(CollectionRowRole.TITLE)) or "")

    def _subtitle_text(self, index: QModelIndex) -> str:
        up_name = index.data(int(CollectionRowRole.UP_NAME)) or "N/A"
        fav_time = index.data(int(CollectionRowRole.FAV_TIME)) or "N/A"
        publish_time = index.data(int(CollectionRowRole.PUBLISH_TIME)) or "N/A"
        play_count = index.data(int(CollectionRowRole.PLAY_COUNT)) or 0
        collect_count = index.data(int(CollectionRowRole.COLLECT_COUNT)) or 0
        danmaku_count = index.data(int(CollectionRowRole.DANMAKU_COUNT)) or 0
        duration = index.data(int(CollectionRowRole.DURATION)) or "N/A"
        return "\n".join(
            [
                strings.COLLECTION_CARD_META_LINE1.format(
                    up_name=up_name,
                    fav_time=fav_time,
                    publish_time=publish_time,
                ),
                strings.COLLECTION_CARD_META_LINE2.format(
                    play_count=play_count,
                    collect_count=collect_count,
                    danmaku_count=danmaku_count,
                    duration=duration,
                ),
            ]
        )

    def _link_text(self, index: QModelIndex) -> str:
        return str(index.data(int(CollectionRowRole.BV_ID)) or "")

    def _expanded_content(self, index: QModelIndex) -> str:
        history = index.data(int(CollectionRowRole.HISTORY)) or []
        rows = sorted(history, key=lambda item: item.get("time") or "", reverse=True)
        lines = [strings.HISTORY_TITLE]
        if not rows:
            lines.append(strings.EMPTY_NO_HISTORY)
        else:
            lines.extend(_history_text(item) for item in rows)
        return "\n".join(lines)

    def _index_key(self, index: QModelIndex) -> object:
        bv_id = index.data(int(CollectionRowRole.BV_ID))
        if bv_id:
            return bv_id
        return super()._index_key(index)

    def sizeHint(self, option, index: QModelIndex) -> QSize: # noqa: N802
        base = super().sizeHint(option, index)
        return QSize(base.width(), max(base.height(), self.cover_height + Spacing.SCALE_32))

    def _text_rect(self, card_rect, content_rect, index):
        cover_rect = QRect(content_rect.left(), content_rect.top(), self.cover_width, self.cover_height)
        text_left = cover_rect.right() + Spacing.SCALE_16
        return QRect(text_left, content_rect.top(), max(0, content_rect.right() - text_left), content_rect.height())

    def _title_color(self, option):
        index = self._paint_index
        is_invalid = bool(index.data(int(CollectionRowRole.IS_INVALID)))
        is_current = bool(index.data(int(CollectionRowRole.IS_CURRENT)))
        is_unfavorited = not is_current and not is_invalid
        is_hover = bool(option.state & QStyle.StateFlag.State_MouseOver)
        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)
        if is_invalid or is_unfavorited:
            return Color.CHARCOAL_WARM.value
        if is_hover or is_selected:
            return Color.TERRACOTTA_BRAND.value
        return Color.ANTHROPIC_NEAR_BLACK.value

    def _configure_title_font(self, font, option, index):
        is_invalid = bool(index.data(int(CollectionRowRole.IS_INVALID)))
        font.setStrikeOut(is_invalid)

    def _paint_extras(self, painter, option, index, content_rect, text_rect, y):
        cover_rect = QRect(content_rect.left(), content_rect.top(), self.cover_width, self.cover_height)
        self._paint_cover(painter, cover_rect, index)
        is_invalid = bool(index.data(int(CollectionRowRole.IS_INVALID)))
        is_current = bool(index.data(int(CollectionRowRole.IS_CURRENT)))
        is_unfavorited = not is_current and not is_invalid
        self._paint_badges(painter, option, text_rect, self._title_y, self._title_height, is_current, is_invalid, is_unfavorited)
        return y

    def _expanded_y_start(self, y, content_rect, index):
        cover_bottom = content_rect.top() + self.cover_height + Spacing.SCALE_12
        return max(y, cover_bottom)

    def _paint_cover(self, painter: QPainter, rect: QRect, index: QModelIndex) -> None:
        cover_path = index.data(int(CollectionRowRole.COVER_PATH))
        pixmap = QPixmap(str(cover_path)) if cover_path else QPixmap()
        if not pixmap.isNull():
            scaled = pixmap.scaled(
                rect.width(),
                rect.height(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            crop_rect = QRect(
                (scaled.width() - rect.width()) // 2,
                (scaled.height() - rect.height()) // 2,
                rect.width(),
                rect.height(),
            )
            clip_path = QPainterPath()
            clip_path.addRoundedRect(rect, BorderRadius.SUBTLE, BorderRadius.SUBTLE)
            painter.setClipPath(clip_path)
            painter.drawPixmap(rect, scaled.copy(crop_rect))
            painter.setClipping(False)
        else:
            painter.setBrush(QColor(Color.WARM_SAND.value))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, BorderRadius.SUBTLE, BorderRadius.SUBTLE)
            icon_color = QColor(Color.CHARCOAL_WARM.value)
            icon_color.setAlpha(51)
            painter.setPen(QPen(icon_color, 2))
            inner_rect = rect.adjusted(20, 15, -20, -15)
            painter.drawRoundedRect(inner_rect, 4, 4)
            tri_size = 12
            tri_x = rect.center().x()
            tri_y = rect.center().y()
            triangle = QPolygon([
                tri_x - tri_size // 2, tri_y - tri_size // 2,
                tri_x - tri_size // 2, tri_y + tri_size // 2,
                tri_x + tri_size // 2, tri_y,
            ])
            painter.setBrush(icon_color)
            painter.drawPolygon(triangle)
        painter.setPen(QPen(QColor(Color.WARM_SAND.value), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(rect, BorderRadius.SUBTLE, BorderRadius.SUBTLE)

    def _paint_badges(
        self,
        painter: QPainter,
        option,
        text_rect: QRect,
        y: int,
        height: int,
        is_current: bool,
        is_invalid: bool,
        is_unfavorited: bool,
    ) -> None:
        badge_font = QFont(option.font)
        badge_font.setPixelSize(Typography.SIZE_LABEL)
        badge_font.setWeight(QFont.Weight.Medium)
        painter.setFont(badge_font)
        badge_x = text_rect.right()
        badges = (
            (strings.COLLECTION_CARD_BADGE_INVALID, Color.ERROR_CRIMSON, is_invalid),
            (strings.COLLECTION_CARD_BADGE_UNFAVORITED, Color.CHARCOAL_WARM, is_unfavorited),
        )
        for label, color, visible in badges:
            if not visible:
                continue
            metrics = painter.fontMetrics()
            width = metrics.horizontalAdvance(label) + Spacing.SCALE_16
            badge_rect = QRect(badge_x - width, y, width, height)
            painter.setPen(QPen(QColor(color.value), 1))
            painter.drawRoundedRect(badge_rect, BorderRadius.SUBTLE, BorderRadius.SUBTLE)
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, label)
            badge_x -= width + Spacing.SCALE_8


class CollectionFolderDelegate(QStyledItemDelegate):
    """Custom delegate for collection folder items — paints name + count in a warm card."""

    _COUNT_ROLE = Qt.ItemDataRole.UserRole + 2

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        card_rect = option.rect.adjusted(
            Spacing.SCALE_8, Spacing.SCALE_6,
            -Spacing.SCALE_8, -Spacing.SCALE_6,
        )
        painter.setBrush(QColor(Color.IVORY.value))
        painter.setPen(QPen(QColor(Color.WARM_SAND.value), 1))
        painter.drawRoundedRect(card_rect, BorderRadius.GENEROUS, BorderRadius.GENEROUS)

        name = index.data(Qt.ItemDataRole.UserRole + 1) or index.data(Qt.ItemDataRole.DisplayRole) or ""
        count = index.data(self._COUNT_ROLE)
        count_text = strings.COLLECTION_VIDEO_COUNT_ONLY.format(count=count) if count is not None else ""

        content_rect = card_rect.adjusted(
            Spacing.CARD_PADDING, 0,
            -Spacing.CARD_PADDING, 0,
        )

        name_font = QFont(option.font)
        name_font.setPixelSize(Typography.SIZE_BODY_STANDARD)
        name_font.setWeight(QFont.Weight.Medium)
        painter.setFont(name_font)
        painter.setPen(QColor(Color.ANTHROPIC_NEAR_BLACK.value))
        name_rect = QRect(content_rect.left(), card_rect.top(), content_rect.width(), card_rect.height())
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, name)

        if count_text:
            count_font = QFont(option.font)
            count_font.setPixelSize(Typography.SIZE_CAPTION)
            painter.setFont(count_font)
            painter.setPen(QColor(Color.CHARCOAL_WARM.value))
            count_width = painter.fontMetrics().horizontalAdvance(count_text)
            count_rect = QRect(
                content_rect.right() - count_width,
                card_rect.top(),
                count_width,
                card_rect.height(),
            )
            painter.drawText(count_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, count_text)

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:  # noqa: N802
        return QSize(option.rect.width() if option.rect.width() > 0 else 320, 48)


class CollectionPage(QWidget):
    """Collection folder browser and card-based detail page."""

    back_requested = Signal()
    collection_selected = Signal(object, str)

    def __init__(self, cache_service: CacheService, parent=None):
        super().__init__(parent)
        self.cache_service = cache_service
        self._current_collection_id = 0

        self.source_model = CollectionRowsModel(parent=self)
        self.collection_list = QListWidget(self)
        self.filter_proxy = CollectionFilterProxyModel(parent=self)
        self.filter_proxy.setSourceModel(self.source_model)
        self.paged_proxy = PagedProxyModel(parent=self)
        self.paged_proxy.setSourceModel(self.filter_proxy)
        self.paged_proxy.setPageSize(50)

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

        header_layout = QHBoxLayout()
        self.back_btn = QPushButton(strings.BTN_BACK)
        self.back_btn.setObjectName("secondary-btn")
        self.header = PageHeader(strings.PAGE_TITLE_COLLECTION)
        self.title_label = self.header.title_label
        header_layout.addWidget(self.back_btn)
        header_layout.addWidget(self.header)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        self.page_stack = QStackedWidget()
        self._setup_list_page()
        self._setup_detail_page()

        layout.addWidget(self.page_stack, stretch=1)
        self.show_collection_list()

    def _setup_list_page(self) -> None:
        self.list_page = QWidget()
        list_layout = QVBoxLayout(self.list_page)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(Spacing.SCALE_16)

        # Sort bar for collection folders
        folder_sort_bar = QHBoxLayout()
        folder_sort_bar.addStretch()
        folder_sort_bar.addWidget(QLabel(strings.LABEL_SORT))
        self.folder_sort_combo = QComboBox()
        self.folder_sort_combo.addItem(strings.SORT_FOLDER_NAME, "name")
        self.folder_sort_combo.addItem(strings.SORT_FOLDER_COUNT_DESC, "count_desc")
        self.folder_sort_combo.addItem(strings.SORT_FOLDER_COUNT_ASC, "count_asc")
        self.folder_sort_combo.currentIndexChanged.connect(self._on_folder_sort_changed)
        folder_sort_bar.addWidget(self.folder_sort_combo)
        list_layout.addLayout(folder_sort_bar)

        self.collection_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.collection_list.setSpacing(Spacing.SCALE_12)
        self.collection_list.setItemDelegate(CollectionFolderDelegate(self.collection_list))
        self.collection_list.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.collection_list.verticalScrollBar().setSingleStep(20)
        list_layout.addWidget(self.collection_list, stretch=1)
        self.collection_empty_state = EmptyState(strings.EMPTY_NO_COLLECTIONS)
        self.collection_empty_state.hide()
        list_layout.addWidget(self.collection_empty_state, stretch=1)
        self.page_stack.addWidget(self.list_page)

    def _setup_detail_page(self) -> None:
        self.detail_page = QWidget()
        detail_layout = QVBoxLayout(self.detail_page)
        detail_layout.setContentsMargins(0, 0, 0, 0)
        detail_layout.setSpacing(Spacing.SCALE_16)

        sort_options = [
            strings.SORT_FAV_DESC,
            strings.SORT_FAV_ASC,
            strings.SORT_PUB_DESC,
            strings.SORT_PUB_ASC,
            strings.SORT_PLAY_DESC,
            strings.SORT_COLLECT_DESC,
            strings.SORT_DANMAKU_DESC,
            strings.SORT_DURATION_DESC,
        ]
        sort_keys = [
            "fav_desc",
            "fav_asc",
            "pub_desc",
            "pub_asc",
            "play_desc",
            "collect_desc",
            "danmaku_desc",
            "duration_desc",
        ]
        self.filter_bar = FilterBar(sort_options)
        self.search_input = self.filter_bar.search_input
        self.search_input.setClearButtonEnabled(True)
        self.sort_combo = self.filter_bar.sort_combo
        for index, key in enumerate(sort_keys):
            self.sort_combo.setItemData(index, key)

        filter_layout = QVBoxLayout()
        filter_layout.addWidget(self.filter_bar)
        filter_row = QHBoxLayout()
        self.current_only_cb = QCheckBox(strings.LABEL_CURRENT_ONLY)
        filter_row.addWidget(self.current_only_cb, alignment=Qt.AlignmentFlag.AlignVCenter)
        filter_row.addSpacing(Spacing.SCALE_24)

        self.fav_start = self._date_edit()
        self.fav_end = self._date_edit()
        self.pub_start = self._date_edit()
        self.pub_end = self._date_edit()
        filter_row.addWidget(QLabel(strings.LABEL_FAV_TIME), alignment=Qt.AlignmentFlag.AlignVCenter)
        filter_row.addWidget(self.fav_start, alignment=Qt.AlignmentFlag.AlignVCenter)
        filter_row.addWidget(QLabel(strings.LABEL_DATE_SEP), alignment=Qt.AlignmentFlag.AlignVCenter)
        filter_row.addWidget(self.fav_end, alignment=Qt.AlignmentFlag.AlignVCenter)
        filter_row.addSpacing(Spacing.SCALE_24)
        filter_row.addWidget(QLabel(strings.LABEL_PUB_TIME), alignment=Qt.AlignmentFlag.AlignVCenter)
        filter_row.addWidget(self.pub_start, alignment=Qt.AlignmentFlag.AlignVCenter)
        filter_row.addWidget(QLabel(strings.LABEL_DATE_SEP), alignment=Qt.AlignmentFlag.AlignVCenter)
        filter_row.addWidget(self.pub_end, alignment=Qt.AlignmentFlag.AlignVCenter)
        filter_row.addStretch()
        self.clear_dates_btn = QPushButton(strings.BTN_CLEAR_DATE_FILTER)
        filter_row.addWidget(self.clear_dates_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        filter_layout.addLayout(filter_row)
        detail_layout.addLayout(filter_layout)

        self.list_view = CardListView()
        self.list_view.setEditTriggers(CardListView.EditTrigger.NoEditTriggers)
        self.list_view.setMouseTracking(True)
        self.list_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.delegate = CollectionVideoCardDelegate(self.list_view)
        self.list_view.setItemDelegate(self.delegate)

        self.pagination_bar = PaginationBar()
        self.list_view.bind_paged_proxy(self.paged_proxy, self.pagination_bar)
        self.prev_btn = self.pagination_bar.prev_button
        self.next_btn = self.pagination_bar.next_button
        self.page_label = self.pagination_bar.page_label

        self.video_empty_state = EmptyState(strings.EMPTY_NO_VIDEOS)
        self.video_empty_state.hide()
        detail_layout.addWidget(self.list_view, stretch=1)
        detail_layout.addWidget(self.video_empty_state, stretch=1)
        detail_layout.addSpacing(Spacing.SCALE_8)
        detail_layout.addWidget(self.pagination_bar)
        self.page_stack.addWidget(self.detail_page)

    def _date_edit(self) -> QDateEdit:
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setSpecialValueText(strings.DATE_UNSELECTED)
        date_edit.setDate(date_edit.minimumDate())
        date_edit.installEventFilter(self)
        return date_edit

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.ChildAdded:
            for cal in obj.findChildren(QCalendarWidget):
                cal.setStyleSheet(get_base_stylesheet())
        return super().eventFilter(obj, event)

    def _connect_signals(self) -> None:
        self.back_btn.clicked.connect(self._on_back_clicked)
        self.collection_list.itemClicked.connect(self._on_collection_item_clicked)
        self.search_input.textChanged.connect(self._on_search_changed)
        self.current_only_cb.toggled.connect(self._on_current_only_changed)
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        self.fav_start.dateChanged.connect(self._update_date_filters)
        self.fav_end.dateChanged.connect(self._update_date_filters)
        self.pub_start.dateChanged.connect(self._update_date_filters)
        self.pub_end.dateChanged.connect(self._update_date_filters)
        self.clear_dates_btn.clicked.connect(self._clear_date_filters)
        self.prev_btn.clicked.connect(self._after_page_change)
        self.next_btn.clicked.connect(self._after_page_change)
        self.list_view.clicked.connect(self._on_list_clicked)
        self.filter_proxy.layoutChanged.connect(self._update_empty_state)
        self.filter_proxy.modelReset.connect(self._update_empty_state)
        self.paged_proxy.layoutChanged.connect(self._update_empty_state)
        self.paged_proxy.modelReset.connect(self._update_empty_state)

    def set_collection_list(self, collections: list[dict[str, Any]]) -> None:
        self._collections_raw = collections
        self._apply_folder_sort()
        self._update_collection_empty_state()
        self.show_collection_list()

    def _apply_folder_sort(self) -> None:
        sort_key = self.folder_sort_combo.currentData() if hasattr(self, 'folder_sort_combo') else "name"
        collections = list(self._collections_raw) if hasattr(self, '_collections_raw') else []
        if sort_key == "count_desc":
            collections.sort(key=lambda c: c.get("media_count", 0), reverse=True)
        elif sort_key == "count_asc":
            collections.sort(key=lambda c: c.get("media_count", 0))
        else:
            collections.sort(key=lambda c: c.get("name", ""))

        self.collection_list.clear()
        for collection in collections:
            name = collection.get("name", "")
            media_count = collection.get("media_count", 0)
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.UserRole, collection.get("id", 0))
            item.setData(Qt.ItemDataRole.UserRole + 1, name)
            item.setData(Qt.ItemDataRole.UserRole + 2, media_count)
            item.setText(name)
            self.collection_list.addItem(item)

    @Slot(int)
    def _on_folder_sort_changed(self, _index: int) -> None:
        self._apply_folder_sort()
        self._update_collection_empty_state()

    def show_collection_list(self) -> None:
        self.page_stack.setCurrentWidget(self.list_page)
        self.header.set_title(strings.PAGE_TITLE_COLLECTION)
        self.back_btn.setEnabled(False)
        self._clear_expanded_cards()
        self._update_collection_empty_state()

    def load_data(self, collection_id: int, title: str, rows: list[dict[str, Any]]) -> None:
        self._current_collection_id = collection_id
        self.header.set_title(strings.COLLECTION_DETAIL_TITLE.format(title=title))
        self.back_btn.setEnabled(True)
        self.page_stack.setCurrentWidget(self.detail_page)

        self.search_input.clear()
        self.current_only_cb.setChecked(False)
        self.sort_combo.setCurrentIndex(0)
        self._clear_date_filters()
        self.source_model.set_rows(rows)
        self.paged_proxy.setCurrentPage(1)
        self._clear_expanded_cards()
        self._update_pagination_ui()
        self._update_empty_state()

    def _on_back_clicked(self) -> None:
        self.back_requested.emit()
        self.show_collection_list()

    def _on_collection_item_clicked(self, item: QListWidgetItem) -> None:
        collection_id = item.data(Qt.ItemDataRole.UserRole)
        if collection_id is None:
            return
        collection_name = item.data(Qt.ItemDataRole.UserRole + 1) or item.text()
        self.collection_selected.emit(collection_id, str(collection_name))

    @Slot(str)
    def _on_search_changed(self, text: str) -> None:
        self.filter_proxy.setSearchText(text)
        self.paged_proxy.setCurrentPage(1)
        self._clear_expanded_cards()
        self._update_pagination_ui()
        self._update_empty_state()

    @Slot(bool)
    def _on_current_only_changed(self, checked: bool) -> None:
        self.filter_proxy.setShowCurrentOnly(checked)
        self.paged_proxy.setCurrentPage(1)
        self._clear_expanded_cards()
        self._update_pagination_ui()
        self._update_empty_state()

    @Slot(int)
    def _on_sort_changed(self, index: int) -> None:
        self.filter_proxy.setSortKey(self.sort_combo.itemData(index))
        self.paged_proxy.setCurrentPage(1)
        self._clear_expanded_cards()
        self._update_pagination_ui()
        self._update_empty_state()

    def _get_datetime_from_qdate(self, qdate: QDateEdit) -> float | None:
        if qdate.date() == qdate.minimumDate():
            return None
        return float(qdate.dateTime().toSecsSinceEpoch())

    @Slot()
    def _update_date_filters(self) -> None:
        self.filter_proxy.setFavoriteDateRange(
            self._get_datetime_from_qdate(self.fav_start),
            self._get_datetime_from_qdate(self.fav_end),
        )
        self.filter_proxy.setPublishDateRange(
            self._get_datetime_from_qdate(self.pub_start),
            self._get_datetime_from_qdate(self.pub_end),
        )
        self.paged_proxy.setCurrentPage(1)
        self._clear_expanded_cards()
        self._update_pagination_ui()
        self._update_empty_state()

    @Slot()
    def _clear_date_filters(self) -> None:
        date_edits = (self.fav_start, self.fav_end, self.pub_start, self.pub_end)
        for date_edit in date_edits:
            date_edit.blockSignals(True)
            date_edit.setDate(date_edit.minimumDate())
            date_edit.blockSignals(False)
        self._update_date_filters()

    @Slot()
    def _after_page_change(self) -> None:
        self._clear_expanded_cards()
        self._update_pagination_ui()
        self._update_empty_state()

    @Slot()
    def _on_prev_page(self) -> None:
        self.paged_proxy.previousPage()
        self._after_page_change()

    @Slot()
    def _on_next_page(self) -> None:
        self.paged_proxy.nextPage()
        self._after_page_change()

    def _update_pagination_ui(self) -> None:
        self.pagination_bar.update(
            current=self.paged_proxy.currentPage(),
            total_pages=self.paged_proxy.pageCount(),
            total_items=self.paged_proxy.totalRowCount(),
        )

    def _update_collection_empty_state(self) -> None:
        has_rows = self.collection_list.count() > 0
        self.collection_list.setVisible(has_rows)
        self.collection_empty_state.setVisible(not has_rows)

    def _update_empty_state(self) -> None:
        has_rows = self.paged_proxy.rowCount() > 0
        self.list_view.setVisible(has_rows)
        self.video_empty_state.setVisible(not has_rows)
        self._update_pagination_ui()

    @Slot(QModelIndex)
    def _on_list_clicked(self, index: QModelIndex) -> None:
        if not index.isValid():
            return
        position = self.list_view.viewport().mapFromGlobal(self.list_view.cursor().pos())
        if self.delegate.hitTestLink(position, index):
            bv_id = index.data(int(CollectionRowRole.BV_ID))
            if bv_id:
                webbrowser.open(f"https://www.bilibili.com/video/{bv_id}")
            return
        self.delegate.toggleExpanded(index)

    def _clear_expanded_cards(self) -> None:
        self.delegate._expanded_rows.clear()
        self.list_view.viewport().update()
