import logging
import os
import webbrowser
from typing import Any

from PySide6.QtCore import QDate, Qt, Signal, Slot
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
    QFormLayout,
    QGroupBox,
)

from app.models import (
    CollectionFilterProxyModel,
    CollectionRowRole,
    CollectionRowsModel,
    PagedProxyModel,
)
from app.services.cache_service import CacheService
from app.theme import BorderRadius, Color, Spacing, Typography

logger = logging.getLogger(__name__)


class HistoryWidget(QWidget):
    """Widget to display the expanded history for a video."""

    def __init__(self, history_data: list[dict[str, Any]], parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            Spacing.SCALE_16, Spacing.SCALE_16, Spacing.SCALE_16, Spacing.SCALE_16
        )
        layout.setSpacing(Spacing.SCALE_8)

        title = QLabel("操作历史")
        title.setStyleSheet(
            f"font-size: {Typography.SIZE_BODY_LARGE}px; font-weight: bold;"
        )
        layout.addWidget(title)

        if not history_data:
            layout.addWidget(QLabel("暂无历史记录"))
        else:
            for item in history_data:
                action = item.get("action", "")
                time = item.get("time", "")
                collection = item.get("collection_name", "")
                action_text = "添加" if action == "add" else "移除"
                color = "green" if action == "add" else "red"
                text = f"[{time}] <font color='{color}'>{action_text}</font> | 收藏夹: {collection}"
                lbl = QLabel(text)
                layout.addWidget(lbl)

        layout.addStretch()
        self.setStyleSheet(
            f"background-color: {Color.IVORY.value}; border: 1px solid {Color.WARM_SAND.value}; border-radius: {BorderRadius.ROUNDED}px;"
        )


class CollectionPage(QWidget):
    """
    The collection detail page with full browser-parity controls.
    Shows search, date filters, current-only toggle, sort choices, pagination, and history expansion.
    """

    back_requested = Signal()

    def __init__(self, cache_service: CacheService, parent=None):
        super().__init__(parent)
        self.cache_service = cache_service
        self._current_collection_id = 0
        self._expanded_row = -1
        self._expanded_widget: HistoryWidget | None = None

        self.source_model = CollectionRowsModel(parent=self)
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
            Spacing.SCALE_24, Spacing.SCALE_24, Spacing.SCALE_24, Spacing.SCALE_24
        )
        layout.setSpacing(Spacing.SCALE_16)

        header_layout = QHBoxLayout()
        self.back_btn = QPushButton("返回")
        self.title_label = QLabel("收藏夹")
        self.title_label.setObjectName("h1")
        header_layout.addWidget(self.back_btn)
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        controls_group = QGroupBox("筛选与排序")
        controls_layout = QVBoxLayout(controls_group)

        row1_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索 标题/BV号/UP主...")
        self.search_input.setClearButtonEnabled(True)

        self.current_only_cb = QCheckBox("仅显示当前有效视频")

        self.sort_combo = QComboBox()
        self.sort_combo.addItem("收藏时间 (降序)", "fav_desc")
        self.sort_combo.addItem("收藏时间 (升序)", "fav_asc")
        self.sort_combo.addItem("发布时间 (降序)", "pub_desc")
        self.sort_combo.addItem("发布时间 (升序)", "pub_asc")
        self.sort_combo.addItem("播放量 (降序)", "play_desc")
        self.sort_combo.addItem("收藏量 (降序)", "collect_desc")
        self.sort_combo.addItem("弹幕数 (降序)", "danmaku_desc")
        self.sort_combo.addItem("时长 (降序)", "duration_desc")

        row1_layout.addWidget(QLabel("搜索:"))
        row1_layout.addWidget(self.search_input, stretch=1)
        row1_layout.addWidget(self.current_only_cb)
        row1_layout.addWidget(QLabel("排序:"))
        row1_layout.addWidget(self.sort_combo)
        controls_layout.addLayout(row1_layout)

        row2_layout = QHBoxLayout()

        self.fav_start = QDateEdit()
        self.fav_start.setCalendarPopup(True)
        self.fav_start.setSpecialValueText("未选择")
        self.fav_start.setDate(self.fav_start.minimumDate())

        self.fav_end = QDateEdit()
        self.fav_end.setCalendarPopup(True)
        self.fav_end.setSpecialValueText("未选择")
        self.fav_end.setDate(self.fav_start.minimumDate())

        self.pub_start = QDateEdit()
        self.pub_start.setCalendarPopup(True)
        self.pub_start.setSpecialValueText("未选择")
        self.pub_start.setDate(self.fav_start.minimumDate())

        self.pub_end = QDateEdit()
        self.pub_end.setCalendarPopup(True)
        self.pub_end.setSpecialValueText("未选择")
        self.pub_end.setDate(self.fav_start.minimumDate())

        row2_layout.addWidget(QLabel("收藏时间:"))
        row2_layout.addWidget(self.fav_start)
        row2_layout.addWidget(QLabel("-"))
        row2_layout.addWidget(self.fav_end)

        row2_layout.addSpacing(Spacing.SCALE_24)

        row2_layout.addWidget(QLabel("发布时间:"))
        row2_layout.addWidget(self.pub_start)
        row2_layout.addWidget(QLabel("-"))
        row2_layout.addWidget(self.pub_end)

        row2_layout.addStretch()

        self.clear_dates_btn = QPushButton("清除日期筛选")
        row2_layout.addWidget(self.clear_dates_btn)

        controls_layout.addLayout(row2_layout)
        layout.addWidget(controls_group)

        self.table = QTableView()
        self.table.setModel(self.paged_proxy)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, self.source_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.table, stretch=1)

        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton("上一页")
        self.next_btn = QPushButton("下一页")
        self.page_label = QLabel("第 1 页 / 共 1 页 (0 个视频)")

        pagination_layout.addStretch()
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addStretch()
        layout.addLayout(pagination_layout)

    def _connect_signals(self) -> None:
        self.back_btn.clicked.connect(self.back_requested)

        self.search_input.textChanged.connect(self._on_search_changed)
        self.current_only_cb.toggled.connect(self._on_current_only_changed)
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)

        self.fav_start.dateChanged.connect(self._update_date_filters)
        self.fav_end.dateChanged.connect(self._update_date_filters)
        self.pub_start.dateChanged.connect(self._update_date_filters)
        self.pub_end.dateChanged.connect(self._update_date_filters)
        self.clear_dates_btn.clicked.connect(self._clear_date_filters)

        self.prev_btn.clicked.connect(self._on_prev_page)
        self.next_btn.clicked.connect(self._on_next_page)

        self.table.clicked.connect(self._on_table_clicked)

    def load_data(
        self, collection_id: int, title: str, rows: list[dict[str, Any]]
    ) -> None:
        self._current_collection_id = collection_id
        self.title_label.setText(f"收藏夹: {title}")

        self.search_input.clear()
        self.current_only_cb.setChecked(False)
        self.sort_combo.setCurrentIndex(0)
        self._clear_date_filters()

        self.source_model.set_rows(rows)
        self.paged_proxy.setCurrentPage(1)
        self._update_pagination_ui()
        self._collapse_history()

    @Slot(str)
    def _on_search_changed(self, text: str) -> None:
        self.filter_proxy.setSearchText(text)
        self.paged_proxy.setCurrentPage(1)
        self._collapse_history()
        self._update_pagination_ui()

    @Slot(bool)
    def _on_current_only_changed(self, checked: bool) -> None:
        self.filter_proxy.setShowCurrentOnly(checked)
        self.paged_proxy.setCurrentPage(1)
        self._collapse_history()
        self._update_pagination_ui()

    @Slot(int)
    def _on_sort_changed(self, index: int) -> None:
        data = self.sort_combo.itemData(index)
        self.filter_proxy.setSortKey(data)
        self.paged_proxy.setCurrentPage(1)
        self._collapse_history()
        self._update_pagination_ui()

    def _get_datetime_from_qdate(self, qdate: QDateEdit) -> float | None:
        if qdate.date() == qdate.minimumDate():
            return None
        return float(qdate.dateTime().toSecsSinceEpoch())

    @Slot()
    def _update_date_filters(self) -> None:
        f_start = self._get_datetime_from_qdate(self.fav_start)
        f_end = self._get_datetime_from_qdate(self.fav_end)
        self.filter_proxy.setFavoriteDateRange(f_start, f_end)

        p_start = self._get_datetime_from_qdate(self.pub_start)
        p_end = self._get_datetime_from_qdate(self.pub_end)
        self.filter_proxy.setPublishDateRange(p_start, p_end)

        self.paged_proxy.setCurrentPage(1)
        self._collapse_history()
        self._update_pagination_ui()

    @Slot()
    def _clear_date_filters(self) -> None:
        self.fav_start.blockSignals(True)
        self.fav_end.blockSignals(True)
        self.pub_start.blockSignals(True)
        self.pub_end.blockSignals(True)

        min_date = self.fav_start.minimumDate()
        self.fav_start.setDate(min_date)
        self.fav_end.setDate(min_date)
        self.pub_start.setDate(min_date)
        self.pub_end.setDate(min_date)

        self.fav_start.blockSignals(False)
        self.fav_end.blockSignals(False)
        self.pub_start.blockSignals(False)
        self.pub_end.blockSignals(False)

        # Manually trigger update
        self._update_date_filters()

    @Slot()
    def _on_prev_page(self) -> None:
        current = self.paged_proxy.currentPage()
        if current > 1:
            self._collapse_history()
            self.paged_proxy.setCurrentPage(current - 1)
            self._update_pagination_ui()

    @Slot()
    def _on_next_page(self) -> None:
        current = self.paged_proxy.currentPage()
        total = self.paged_proxy.pageCount()
        if current < total:
            self._collapse_history()
            self.paged_proxy.setCurrentPage(current + 1)
            self._update_pagination_ui()

    def _update_pagination_ui(self) -> None:
        current = self.paged_proxy.currentPage()
        total_pages = self.paged_proxy.pageCount()

        # Ensure proxy logic correctly counts current filtered items
        total_items = (
            self.paged_proxy.rowCount() if self.paged_proxy.sourceModel() else 0
        )

        # Get true row count from filter proxy
        if self.filter_proxy:
            total_items = self.filter_proxy.rowCount()

        if total_pages == 0:
            total_pages = 1

        self.page_label.setText(
            f"第 {current} 页 / 共 {total_pages} 页 ({total_items} 个视频)"
        )
        self.prev_btn.setEnabled(current > 1)
        self.next_btn.setEnabled(current < total_pages)

    @Slot()
    def _on_table_clicked(self, index) -> None:
        # Check if clicking bv_id column
        if index.column() == 1:
            bv_id = self.paged_proxy.data(index, Qt.ItemDataRole.DisplayRole)
            if bv_id:
                url = f"https://www.bilibili.com/video/{bv_id}"
                webbrowser.open(url)
            return

        row = index.row()

        # Toggle history on other columns
        if self._expanded_row == row:
            self._collapse_history()
        else:
            self._collapse_history()
            self._expand_history(row)

    def _expand_history(self, row: int) -> None:
        index = self.paged_proxy.index(row, 0)
        history_data = self.paged_proxy.data(index, int(CollectionRowRole.HISTORY))

        if not history_data:
            history_data = []

        self._expanded_widget = HistoryWidget(history_data)
        self.table.setIndexWidget(index, self._expanded_widget)
        self.table.setRowHeight(row, 200)
        self._expanded_row = row

    def _collapse_history(self) -> None:
        if self._expanded_row != -1:
            index = self.paged_proxy.index(self._expanded_row, 0)
            self.table.setIndexWidget(index, None)
            self.table.setRowHeight(
                self._expanded_row, self.table.verticalHeader().defaultSectionSize()
            )
            self._expanded_row = -1
            if self._expanded_widget:
                self._expanded_widget.deleteLater()
                self._expanded_widget = None
