from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QListWidget,
    QStackedWidget,
)

from app.theme import get_base_stylesheet
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.collection_page import CollectionPage
from app.ui.pages.search_page import SearchPage
from app.ui.pages.up_list_page import UpListPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.pages.crawl_page import CrawlPage
from app.ui.pages.downloads_page import DownloadsPage
from app.services.cache_service import CacheService
from database import get_db_path
import sqlite3


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bilibili Personal Collect")
        self.resize(1200, 800)
        self.setStyleSheet(get_base_stylesheet())

        self.db_conn = sqlite3.connect(get_db_path())
        self.db_conn.row_factory = sqlite3.Row
        self.cache_service = CacheService()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QHBoxLayout(self.central_widget)

        self.nav_list = QListWidget()
        self.nav_list.setFixedWidth(200)
        self.nav_list.addItems(
            [
                "Dashboard",
                "Collection",
                "Search",
                "UPs",
                "Settings",
                "Crawl",
                "Downloads",
            ]
        )

        self.pages_stack = QStackedWidget()

        self.dashboard_page = DashboardPage(self.db_conn)
        self.collection_page = CollectionPage(self.cache_service)
        self.search_page = SearchPage(self.cache_service)
        self.up_list_page = UpListPage()
        self.settings_page = SettingsPage()
        self.crawl_page = CrawlPage()
        self.downloads_page = DownloadsPage()

        self.pages_stack.addWidget(self.dashboard_page)
        self.pages_stack.addWidget(self.collection_page)
        self.pages_stack.addWidget(self.search_page)
        self.pages_stack.addWidget(self.up_list_page)
        self.pages_stack.addWidget(self.settings_page)
        self.pages_stack.addWidget(self.crawl_page)
        self.pages_stack.addWidget(self.downloads_page)

        self.layout.addWidget(self.nav_list)
        self.layout.addWidget(self.pages_stack)

        self.nav_list.currentRowChanged.connect(self.pages_stack.setCurrentIndex)
        self.nav_list.setCurrentRow(0)
