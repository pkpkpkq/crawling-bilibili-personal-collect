import pytest
from PySide6.QtCore import Qt
from app.ui.pages.search_page import SearchPage
from app.services.cache_service import CacheService


def test_search_page_initialization(qtbot):
    cache = CacheService()
    page = SearchPage(cache_service=cache)
    qtbot.addWidget(page)

    assert page.title_label.text() == "全局搜索"
    assert page.search_input.placeholderText() == "搜索 标题/BV号/UP主..."
    assert page.sort_combo.count() == 2


def test_search_page_load_data(qtbot):
    cache = CacheService()
    page = SearchPage(cache_service=cache)
    qtbot.addWidget(page)

    rows = [
        {
            "bvid": "BV1xx411c7m9",
            "info": {
                "title": "Test Video",
                "up_name": "Test UP",
                "is_invalid": False,
                "is_unfavorited": False,
            },
            "latest_collection": "My Favs",
            "latest_fav_time": 1600000000.0,
        }
    ]

    page.load_data(rows)
    assert page.source_model.rowCount() == 1
    assert page.paged_proxy.rowCount() == 1


def test_search_page_pagination(qtbot):
    cache = CacheService()
    page = SearchPage(cache_service=cache)
    qtbot.addWidget(page)

    rows = [{"bvid": f"BV{i}"} for i in range(150)]
    page.load_data(rows)

    assert page.paged_proxy.pageCount() == 3
    assert page.paged_proxy.currentPage() == 1
    assert page.paged_proxy.rowCount() == 50

    page.next_btn.click()
    assert page.paged_proxy.currentPage() == 2
