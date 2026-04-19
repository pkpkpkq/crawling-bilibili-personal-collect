import webbrowser
from typing import Any

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QStyledItemDelegate,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from app.models import (
    GlobalSearchFilterProxyModel,
    GlobalSearchRowRole,
    GlobalSearchRowsModel,
    PagedProxyModel,
)
from app.services.cache_service import CacheService
from app.theme import Color, Spacing


class SearchRowDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)

        is_invalid = index.data(int(GlobalSearchRowRole.IS_INVALID))
        is_unfavorited = index.data(int(GlobalSearchRowRole.IS_UNFAVORITED))

        if is_invalid or is_unfavorited:
            option.palette.setColor(
                option.palette.ColorRole.Text, Color.CHARCOAL_WARM.value
            )
            if is_invalid:
                font = option.font
                font.setStrikeOut(True)
                option.font = font


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

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            Spacing.SCALE_24, Spacing.SCALE_24, Spacing.SCALE_24, Spacing.SCALE_24
        )
        layout.setSpacing(Spacing.SCALE_16)

        self.title_label = QLabel("全局搜索")
        self.title_label.setObjectName("h1")
        layout.addWidget(self.title_label)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(Spacing.SCALE_16)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索 标题/BV号/UP主...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self.filter_proxy.setSearchText)
        controls_layout.addWidget(self.search_input, stretch=1)

        self.sort_combo = QComboBox()
        self.sort_combo.addItem("最新收藏时间 (降序)", True)
        self.sort_combo.addItem("最新收藏时间 (升序)", False)
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        controls_layout.addWidget(self.sort_combo)

        layout.addLayout(controls_layout)

        self.table = QTableView()
        self.table.setModel(self.paged_proxy)
        self.table.setItemDelegate(SearchRowDelegate(self.table))
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().hide()

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, self.source_model.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)

        self.table.clicked.connect(self._on_table_clicked)
        layout.addWidget(self.table, stretch=1)

        pagination_layout = QHBoxLayout()
        self.prev_btn = QPushButton("上一页")
        self.prev_btn.clicked.connect(self.paged_proxy.previousPage)
        self.prev_btn.setEnabled(False)

        self.page_label = QLabel("1 / 1")
        self.page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.next_btn = QPushButton("下一页")
        self.next_btn.clicked.connect(self.paged_proxy.nextPage)
        self.next_btn.setEnabled(False)

        pagination_layout.addStretch()
        pagination_layout.addWidget(self.prev_btn)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_btn)
        pagination_layout.addStretch()

        layout.addLayout(pagination_layout)

        self.filter_proxy.layoutChanged.connect(self._update_pagination)
        self.filter_proxy.rowsInserted.connect(self._update_pagination)
        self.filter_proxy.rowsRemoved.connect(self._update_pagination)
        self.paged_proxy.layoutChanged.connect(self._update_pagination)

    def load_data(self, rows: list[dict[str, Any]]) -> None:
        self.source_model.set_rows(rows)
        self._update_pagination()

    def _on_sort_changed(self, index: int) -> None:
        descending = self.sort_combo.itemData(index)
        self.filter_proxy.setSortByLatestFavorite(bool(descending))

    def _update_pagination(self) -> None:
        current = self.paged_proxy.currentPage()
        total = self.paged_proxy.pageCount()
        self.page_label.setText(f"{current} / {total}")
        self.prev_btn.setEnabled(current > 1)
        self.next_btn.setEnabled(current < total)

    def _on_table_clicked(self, index: QModelIndex) -> None:
        if not index.isValid():
            return

        column = index.column()
        source_index = self.paged_proxy.mapToSource(index)
        global_index = self.filter_proxy.mapToSource(source_index)

        if column == 1:
            bv_id = self.source_model.data(global_index, int(GlobalSearchRowRole.BV_ID))
            if bv_id:
                url = f"https://www.bilibili.com/video/{bv_id}"
                webbrowser.open(url)
                return

        if column == 2:
            up_id = self.source_model.data(global_index, int(GlobalSearchRowRole.UP_ID))
            if up_id:
                url = f"https://space.bilibili.com/{up_id}"
                webbrowser.open(url)
                return
