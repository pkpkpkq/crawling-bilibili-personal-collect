"""Screenshot evidence tests — grab every page and the main shell offscreen.

Saves PNG files under .sisyphus/evidence/ for visual audit.
Uses QT_QPA_PLATFORM=offscreen (set in conftest.py) so no display is needed.
"""

import os
from pathlib import Path

import pytest

from app.services.cache_service import CacheService
from app.ui.main_window import MainWindow
from app.ui.pages.crawl_page import CrawlPage
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.downloads_page import DownloadsPage
from app.ui.pages.search_page import SearchPage
from app.ui.pages.settings_page import SettingsPage
from app.ui.pages.up_list_page import UpListPage
from app.ui.pages.collection_page import CollectionPage

EVIDENCE_DIR = Path(__file__).resolve().parents[1] / ".sisyphus" / "evidence"


class _MockConn:
    """Minimal mock DB connection for DashboardPage."""

    def cursor(self):
        return _MockCursor()

    def commit(self):
        pass

    def close(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class _MockCursor:
    def execute(self, sql, params=None):
        return self

    def fetchall(self):
        return []

    def fetchone(self):
        return {}

    def close(self):
        pass


def _mock_stats():
    return {
        "total_videos": 100,
        "total_collections": 5,
        "total_ups": 20,
        "following_ups": 10,
        "invalid_videos": 2,
        "collection_counts": [{"name": "Col 1", "count": 50}],
        "top_ups": [{"name": "UP 1", "mid": 1, "count": 10}],
        "monthly_trend": [{"month": "2023-10", "count": 5}],
        "recent_invalid": [
            {"title": "Inv 1", "bv_id": "BV1", "up_name": "UP 1", "collection": "Col 1"}
        ],
        "recent_unfav": [
            {
                "title": "Unf 1",
                "bv_id": "BV2",
                "up_name": "UP 2",
                "collection": "Col 1",
                "unfav_time": "2023",
            }
        ],
        "duration_distribution": {"<1分钟": 10, "1-5分钟": 90},
        "crawl_history": [],
    }


def _grab_and_save(widget, name: str, qapp) -> None:
    """Resize, grab, and save widget screenshot to evidence dir."""
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    widget.resize(1200, 800)
    path = str(EVIDENCE_DIR / f"{name}.png")
    widget.grab().save(path)
    assert Path(path).exists(), f"Screenshot not saved: {path}"
    assert Path(path).stat().st_size > 0, f"Screenshot is empty: {path}"


# --- Individual page screenshots ---

def test_screenshot_dashboard_page(qapp, mocker):
    mocker.patch("app.repositories.stats.get_stats", lambda conn: _mock_stats())
    page = DashboardPage(db_conn=_MockConn())
    _grab_and_save(page, "dashboard_page", qapp)


def test_screenshot_collection_page(qapp):
    cache = CacheService()
    page = CollectionPage(cache_service=cache)
    _grab_and_save(page, "collection_page", qapp)


def test_screenshot_search_page(qapp):
    cache = CacheService()
    page = SearchPage(cache_service=cache)
    _grab_and_save(page, "search_page", qapp)


def test_screenshot_up_list_page(qapp):
    page = UpListPage()
    _grab_and_save(page, "up_list_page", qapp)


def test_screenshot_settings_page(qapp, mocker):
    mocker.patch(
        "app.services.config_service.load_config",
        return_value=("123", "cookie", {}),
    )
    page = SettingsPage()
    _grab_and_save(page, "settings_page", qapp)


def test_screenshot_crawl_page(qapp):
    page = CrawlPage()
    _grab_and_save(page, "crawl_page", qapp)


def test_screenshot_downloads_page(qapp, mocker):
    mock_service = mocker.MagicMock()
    mock_service.get_latest_collections.return_value = []
    page = DownloadsPage(download_service=mock_service, db_path=":memory:")
    _grab_and_save(page, "downloads_page", qapp)


# --- Main window with page navigation screenshots ---

def test_screenshot_main_shell(qapp):
    window = MainWindow()
    window.resize(1200, 800)
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    path = str(EVIDENCE_DIR / "main_window_shell.png")
    window.grab().save(path)
    assert Path(path).exists()
    assert Path(path).stat().st_size > 0


def test_screenshot_main_window_each_nav_page(qapp, seeded_fixture_db, monkeypatch):
    """Navigate each sidebar row and grab the visible page."""
    monkeypatch.setattr("app.ui.main_window.get_db_path", lambda: str(seeded_fixture_db))
    window = MainWindow()
    window.resize(1200, 800)

    page_names = [
        "dashboard",
        "collection",
        "search",
        "ups",
        "settings",
        "crawl",
        "downloads",
    ]

    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

    for row, name in enumerate(page_names):
        window.nav_list.setCurrentRow(row)
        current = window.pages_stack.currentWidget()
        path = str(EVIDENCE_DIR / f"main_window_{name}.png")
        current.grab().save(path)
        assert Path(path).exists(), f"Missing screenshot for {name}"
        assert Path(path).stat().st_size > 0, f"Empty screenshot for {name}"
