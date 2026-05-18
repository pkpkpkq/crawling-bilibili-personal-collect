from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Slot, Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
)

from app.repositories import (
    get_all_collections,
    get_all_videos_index,
    get_videos_in_collection,
)
from app.repositories.connection import get_connection
from app.repositories.following import get_all_following_ups
from app.services.cache_service import CacheService
from app.theme import get_base_stylesheet, Color, Spacing, BorderRadius, Typography
from app.ui.pages.crawl_page import CrawlPage
from app.ui.pages.collection_page import CollectionPage
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.downloads_page import DownloadsPage
from app.ui.pages.search_page import SearchPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.pages.up_list_page import UpListPage
from app.ui.strings import (
    WINDOW_TITLE,
    NAV_DATA_OVERVIEW,
    NAV_COLLECTION,
    NAV_GLOBAL_SEARCH,
    NAV_FOLLOWING_UP,
    NAV_SETTINGS,
    NAV_CRAWL,
    NAV_DOWNLOADS,
)
from database import get_db_path
import sqlite3


# Page indices matching nav_list order
_PAGE_DASHBOARD = 0
_PAGE_COLLECTION = 1
_PAGE_SEARCH = 2
_PAGE_UPS = 3
_PAGE_SETTINGS = 4
_PAGE_CRAWL = 5
_PAGE_DOWNLOADS = 6

_ICONS_DIR = Path(__file__).parent / "icons"


def _tinted_icon(svg_path: str, color: str, size: int = 20) -> QPixmap:
    """Render an SVG file tinted to the given color."""
    renderer = QSvgRenderer(svg_path)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
    painter.fillRect(pixmap.rect(), QColor(color))
    painter.end()
    return pixmap


def _make_nav_icon(svg_filename: str) -> QIcon:
    """Build a QIcon with normal and selected state colours."""
    svg_path = str(_ICONS_DIR / svg_filename)
    icon = QIcon()
    normal = _tinted_icon(svg_path, Color.OLIVE_GRAY.value)
    selected = _tinted_icon(svg_path, Color.IVORY.value)
    hover = _tinted_icon(svg_path, Color.ANTHROPIC_NEAR_BLACK.value)
    icon.addPixmap(normal, QIcon.Mode.Normal, QIcon.State.Off)
    icon.addPixmap(selected, QIcon.Mode.Selected, QIcon.State.Off)
    icon.addPixmap(selected, QIcon.Mode.Active, QIcon.State.On)
    icon.addPixmap(hover, QIcon.Mode.Active, QIcon.State.Off)
    return icon


def _nav_stylesheet() -> str:
    """Warm-themed navigation panel stylesheet with icon+text labels."""
    return f"""
        QWidget#nav-panel {{
            background-color: {Color.IVORY.value};
            border-right: 1px solid {Color.BORDER_CREAM.value};
        }}
        QLabel#nav-brand {{
            font-family: {Typography.FONT_FAMILY_SERIF};
            font-size: {Typography.SIZE_BODY_NAV}px;
            font-weight: 500;
            color: {Color.CHARCOAL_WARM.value};
            padding: {Spacing.SCALE_16}px;
            padding-bottom: {Spacing.SCALE_8}px;
            background: transparent;
        }}
        QListWidget {{
            background-color: transparent;
            border: none;
            padding: 0px;
            outline: none;
        }}
        QListWidget::item {{
            color: {Color.OLIVE_GRAY.value};
            padding: {Spacing.SCALE_10}px {Spacing.SCALE_16}px;
            padding-left: {Spacing.SCALE_12}px;
            border: none;
            margin: 2px {Spacing.SCALE_6}px;
            border-radius: {BorderRadius.GENEROUS}px;
            font-size: {Typography.SIZE_BODY_STANDARD}px;
        }}
        QListWidget::item:hover {{
            background-color: {Color.WARM_SAND.value};
            color: {Color.ANTHROPIC_NEAR_BLACK.value};
        }}
        QListWidget::item:selected {{
            background-color: {Color.TERRACOTTA_BRAND.value};
            color: {Color.IVORY.value};
            font-weight: 500;
        }}
    """


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(1200, 800)
        self.setStyleSheet(get_base_stylesheet())

        self.db_conn = sqlite3.connect(get_db_path())
        self.db_conn.row_factory = sqlite3.Row
        self.cache_service = CacheService()
        self._video_index = get_all_videos_index(self.db_conn, self.cache_service)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # --- Navigation panel ---
        nav_panel = QWidget()
        nav_panel.setObjectName("nav-panel")
        nav_panel.setFixedWidth(210)
        nav_panel.setStyleSheet(_nav_stylesheet())

        nav_layout = QVBoxLayout(nav_panel)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(0)

        nav_brand = QLabel("Bilibili 收藏管理")
        nav_brand.setObjectName("nav-brand")
        nav_layout.addWidget(nav_brand)

        self.nav_list = QListWidget()
        self.nav_list.setObjectName("nav-list")
        self.nav_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.nav_list.setIconSize(QSize(20, 20))

        nav_items = [
            (NAV_DATA_OVERVIEW, _PAGE_DASHBOARD, "nav_dashboard.svg"),
            (NAV_COLLECTION, _PAGE_COLLECTION, "nav_collection.svg"),
            (NAV_GLOBAL_SEARCH, _PAGE_SEARCH, "nav_search.svg"),
            (NAV_FOLLOWING_UP, _PAGE_UPS, "nav_following.svg"),
            (NAV_SETTINGS, _PAGE_SETTINGS, "nav_settings.svg"),
            (NAV_CRAWL, _PAGE_CRAWL, "nav_crawl.svg"),
            (NAV_DOWNLOADS, _PAGE_DOWNLOADS, "nav_download.svg"),
        ]
        for label, _, icon_file in nav_items:
            item = QListWidgetItem(_make_nav_icon(icon_file), label)
            item.setSizeHint(QSize(0, 44))
            self.nav_list.addItem(item)

        nav_layout.addWidget(self.nav_list)
        nav_layout.addStretch()

        # --- Page stack ---
        self.pages_stack = QStackedWidget()
        self.pages_stack.setObjectName("page-stack")

        self.dashboard_page = DashboardPage(self.db_conn)
        self.dashboard_page.setObjectName("page-dashboard")
        self.collection_page = CollectionPage(self.cache_service)
        self.collection_page.setObjectName("page-collection")
        self.search_page = SearchPage(self.cache_service)
        self.search_page.setObjectName("page-search")
        self.up_list_page = UpListPage()
        self.up_list_page.setObjectName("page-ups")
        self.settings_page = SettingsPage()
        self.settings_page.setObjectName("page-settings")
        self.crawl_page = CrawlPage()
        self.crawl_page.setObjectName("page-crawl")
        self.downloads_page = DownloadsPage()
        self.downloads_page.setObjectName("page-downloads")

        self.pages_stack.addWidget(self.dashboard_page)
        self.pages_stack.addWidget(self.collection_page)
        self.pages_stack.addWidget(self.search_page)
        self.pages_stack.addWidget(self.up_list_page)
        self.pages_stack.addWidget(self.settings_page)
        self.pages_stack.addWidget(self.crawl_page)
        self.pages_stack.addWidget(self.downloads_page)

        self.layout.addWidget(nav_panel)
        self.layout.addWidget(self.pages_stack, stretch=1)

        # --- Connect signals ---
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        self.dashboard_page.search_requested.connect(self._on_dashboard_search_requested)
        self.collection_page.collection_selected.connect(self._open_collection)
        self.collection_page.download_requested.connect(self._on_download_requested)
        self.collection_page.collection_download_requested.connect(self._on_collection_download_requested)
        self.up_list_page.search_requested.connect(self._on_up_search_requested)
        self.crawl_page.crawl_completed.connect(self._on_crawl_completed)
        self.settings_page.settings_saved.connect(self._on_settings_saved)

        # --- Initial data load ---
        self._load_search_data()
        self.nav_list.setCurrentRow(0)

    # ------------------------------------------------------------------
    # Data loading helpers
    # ------------------------------------------------------------------

    def _rebuild_video_index(self) -> None:
        """Rebuild the global video index from the database."""
        self._video_index = get_all_videos_index(self.db_conn, self.cache_service)

    def _load_search_data(self) -> None:
        """Load the global search page with current video index data."""
        self.search_page.load_data(list(self._video_index.values()))

    def _load_up_list(self) -> None:
        """Load the UP list page from the database."""
        self.up_list_page.load_data()

    def _load_collection_list(self) -> None:
        """Load collection list with video count metadata."""
        collections = get_all_collections(self.db_conn)
        self.collection_page.set_collection_list(collections)

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def _on_nav_changed(self, row: int) -> None:
        self.pages_stack.setCurrentIndex(row)

        if row == _PAGE_DASHBOARD:
            self.dashboard_page.refresh_data()
        elif row == _PAGE_COLLECTION:
            self._load_collection_list()
            self.collection_page.show_collection_list()
        elif row == _PAGE_SEARCH:
            # Data is already loaded; just ensure it's up to date
            if self.search_page.source_model.rowCount() == 0:
                self._load_search_data()
        elif row == _PAGE_UPS:
            self._load_up_list()

    # ------------------------------------------------------------------
    # Collection detail
    # ------------------------------------------------------------------

    @staticmethod
    def _format_collection_time(value):
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value).strftime("%Y-%m-%d %H:%M:%S")
        return value

    @Slot(object, str)
    def _open_collection(self, collection_id: object, title: str) -> None:
        rows = get_videos_in_collection(self.db_conn, collection_id)

        enriched_rows = []
        for row in rows:
            row_dict = dict(row)
            video_data = self._video_index.get(row_dict["bv_id"], {})
            row_dict["fav_time"] = self._format_collection_time(row_dict.get("fav_time"))
            row_dict["publish_time"] = self._format_collection_time(
                row_dict.get("publish_time")
            )
            row_dict["history"] = video_data.get("history", [])
            row_dict["latest_collection"] = video_data.get(
                "latest_collection", row_dict.get("collection_name", "N/A")
            )
            row_dict["cover_path"] = self.cache_service.get_cover_file_path(
                row_dict["bv_id"]
            )
            enriched_rows.append(row_dict)

        self.collection_page.load_data(collection_id, title, enriched_rows)

    # ------------------------------------------------------------------
    # UP → Search handoff
    # ------------------------------------------------------------------

    @Slot(str)
    def _on_up_search_requested(self, up_name: str) -> None:
        """Switch to search page and pre-filter by UP name."""
        self.nav_list.setCurrentRow(_PAGE_SEARCH)
        self.search_page.set_search_text(up_name)

    # ------------------------------------------------------------------
    # Post-crawl refresh
    # ------------------------------------------------------------------

    @Slot(object)
    def _on_crawl_completed(self, result) -> None:
        """Refresh data across all pages after a crawl completes."""
        self._rebuild_video_index()
        self._load_search_data()
        # Dashboard will refresh on next nav to it

    # ------------------------------------------------------------------
    # Settings saved
    # ------------------------------------------------------------------

    @Slot()
    def _on_settings_saved(self) -> None:
        """Handle settings save — could refresh config-dependent state."""
        pass  # Currently no runtime state depends on config changes

    # ------------------------------------------------------------------
    # Download handoff (from context menu → download page)
    # ------------------------------------------------------------------

    @Slot(str)
    def _on_download_requested(self, bv_id: str) -> None:
        """Switch to downloads page and pre-fill BV ID for single-video mode."""
        self.nav_list.setCurrentRow(_PAGE_DOWNLOADS)
        self.downloads_page.mode_combo.setCurrentIndex(0)  # "single" mode
        self.downloads_page.single_bv_input.setText(bv_id)

    @Slot(object)
    def _on_collection_download_requested(self, collection_id: object) -> None:
        """Switch to downloads page and pre-select collection for collection-download mode."""
        self.nav_list.setCurrentRow(_PAGE_DOWNLOADS)
        self.downloads_page.mode_combo.setCurrentIndex(1)  # "collection" mode
        
        # Find the collection in the combo box and set it
        combo = self.downloads_page.collection_combo
        for i in range(combo.count()):
            if combo.itemData(i) == collection_id:
                combo.setCurrentIndex(i)
                break

    # ------------------------------------------------------------------
    # Dashboard insight → search page handoff
    # ------------------------------------------------------------------

    @Slot(str)
    def _on_dashboard_search_requested(self, text: str) -> None:
        """Switch to search page and pre-fill search text from dashboard insight."""
        self.nav_list.setCurrentRow(_PAGE_SEARCH)
        self.search_page.set_search_text(text)
