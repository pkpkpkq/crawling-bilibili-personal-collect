from app.services.cache_service import CacheService
from app.ui.pages.search_page import SearchPage
from app.ui.strings import PAGINATION_FORMAT


def test_search_page_empty_state(qtbot):
    cache = CacheService()
    page = SearchPage(cache_service=cache)
    qtbot.addWidget(page)

    page.load_data([])
    assert page.paged_proxy.rowCount() == 0

    assert page.pagination_bar.page_label.text() == PAGINATION_FORMAT.format(
        current=1,
        total_pages=1,
        total_items=0,
    )
    assert not page.pagination_bar.prev_button.isEnabled()
    assert not page.pagination_bar.next_button.isEnabled()
    assert page.list_view.isHidden()
    assert not page.empty_state.isHidden()


def test_search_page_no_results(qtbot):
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
    assert page.paged_proxy.rowCount() == 1

    page.search_input.setText("No Match")
    assert page.paged_proxy.rowCount() == 0
    assert page.pagination_bar.page_label.text() == PAGINATION_FORMAT.format(
        current=1,
        total_pages=1,
        total_items=0,
    )
    assert page.list_view.isHidden()
    assert not page.empty_state.isHidden()
