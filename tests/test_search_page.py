from app.services.cache_service import CacheService
from app.ui.pages.search_page import SearchPage, SearchVideoCardDelegate
from app.ui.strings import (
    EMPTY_NO_DATA,
    PAGE_TITLE_GLOBAL_SEARCH,
    PLACEHOLDER_SEARCH_GENERAL,
    SORT_LATEST_FAV_ASC,
    SORT_LATEST_FAV_DESC,
)


def test_search_page_initialization(qtbot):
    cache = CacheService()
    page = SearchPage(cache_service=cache)
    qtbot.addWidget(page)

    assert page.title_label.text() == PAGE_TITLE_GLOBAL_SEARCH
    assert page.search_input.placeholderText() == PLACEHOLDER_SEARCH_GENERAL
    assert page.sort_combo.count() == 4
    assert page.sort_combo.itemText(0) == SORT_LATEST_FAV_DESC
    assert page.sort_combo.itemText(1) == SORT_LATEST_FAV_ASC
    assert page.list_view.model() is page.paged_proxy
    assert isinstance(page.delegate, SearchVideoCardDelegate)
    assert page.empty_state.title_label.text() == EMPTY_NO_DATA


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
    assert not page.list_view.isHidden()
    assert page.empty_state.isHidden()


def test_search_page_pagination(qtbot):
    cache = CacheService()
    page = SearchPage(cache_service=cache)
    qtbot.addWidget(page)

    rows = [{"bvid": f"BV{i}"} for i in range(150)]
    page.load_data(rows)

    assert page.paged_proxy.pageCount() == 3
    assert page.paged_proxy.currentPage() == 1
    assert page.paged_proxy.rowCount() == 50

    page.pagination_bar.next_button.click()
    assert page.paged_proxy.currentPage() == 2


def test_search_page_empty_state_for_no_matches(qtbot):
    cache = CacheService()
    page = SearchPage(cache_service=cache)
    qtbot.addWidget(page)

    page.load_data([
        {
            "bvid": "BV1xx411c7m9",
            "info": {"title": "Test Video", "up_name": "Test UP"},
            "latest_collection": "My Favs",
            "latest_fav_time": 1600000000.0,
        }
    ])

    page.set_search_text("missing")

    assert page.paged_proxy.rowCount() == 0
    assert page.list_view.isHidden()
    assert not page.empty_state.isHidden()
