from app.ui.pages.search_page import SearchPage
from app.services.cache_service import CacheService


def test_search_page_empty_state(qtbot):
    cache = CacheService()
    page = SearchPage(cache_service=cache)
    qtbot.addWidget(page)

    page.load_data([])
    assert page.paged_proxy.rowCount() == 0

    assert page.page_label.text() == "1 / 1"
    assert not page.prev_btn.isEnabled()
    assert not page.next_btn.isEnabled()


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
    assert page.page_label.text() == "1 / 1"
