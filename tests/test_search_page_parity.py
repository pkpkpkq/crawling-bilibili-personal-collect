from app.ui.pages.search_page import SearchPage
from app.services.cache_service import CacheService
import pytest


@pytest.fixture
def sample_rows():
    return [
        {
            "bvid": "BV1xx",
            "info": {
                "title": "Title One",
                "up_name": "Up A",
                "is_invalid": False,
                "is_unfavorited": False,
            },
            "latest_collection": "My Favs",
            "latest_fav_time": "2023-01-01 10:00:00",
        },
        {
            "bvid": "BV2yy",
            "info": {
                "title": "Title Two",
                "up_name": "Up B",
                "is_invalid": True,
                "is_unfavorited": False,
            },
            "latest_collection": "Dev",
            "latest_fav_time": "2023-02-01 10:00:00",
        },
        {
            "bvid": "BV3zz",
            "info": {
                "title": "Unfav Video",
                "up_name": "Up C",
                "is_invalid": False,
                "is_unfavorited": True,
            },
            "latest_collection": "Dev",
            "latest_fav_time": "2023-03-01 10:00:00",
        },
    ]


def test_search_page_keyword_matching(qtbot, sample_rows):
    cache = CacheService()
    page = SearchPage(cache_service=cache)
    qtbot.addWidget(page)

    page.load_data(sample_rows)
    assert page.paged_proxy.rowCount() == 3

    page.search_input.setText("One")
    assert page.paged_proxy.rowCount() == 1
    assert page.paged_proxy.data(page.paged_proxy.index(0, 0)) == "Title One"

    page.search_input.setText("BV2")
    assert page.paged_proxy.rowCount() == 1
    assert page.paged_proxy.data(page.paged_proxy.index(0, 0)) == "Title Two"


def test_search_page_latest_favorite_ordering(qtbot, sample_rows):
    cache = CacheService()
    page = SearchPage(cache_service=cache)
    qtbot.addWidget(page)

    page.load_data(sample_rows)
    page.sort_combo.setCurrentIndex(0)
    assert page.paged_proxy.data(page.paged_proxy.index(0, 0)) == "Unfav Video"

    page.sort_combo.setCurrentIndex(1)
    assert page.paged_proxy.data(page.paged_proxy.index(0, 0)) == "Title One"


def test_search_page_metadata_displayed(qtbot, sample_rows):
    cache = CacheService()
    page = SearchPage(cache_service=cache)
    qtbot.addWidget(page)

    page.load_data(sample_rows)

    col_collection = 3
    col_fav_time = 4

    page.sort_combo.setCurrentIndex(1)

    assert page.paged_proxy.data(page.paged_proxy.index(0, col_collection)) == "My Favs"
    assert (
        page.paged_proxy.data(page.paged_proxy.index(0, col_fav_time))
        == "2023-01-01 10:00:00"
    )


def test_search_page_click_through(qtbot, sample_rows, monkeypatch):
    cache = CacheService()
    page = SearchPage(cache_service=cache)
    qtbot.addWidget(page)

    page.load_data(sample_rows)
    page.sort_combo.setCurrentIndex(1)

    opened_url = None

    def mock_open(url):
        nonlocal opened_url
        opened_url = url

    import webbrowser

    monkeypatch.setattr(webbrowser, "open", mock_open)

    index_bv = page.paged_proxy.index(0, 1)
    page._on_table_clicked(index_bv)
    assert opened_url == "https://www.bilibili.com/video/BV1xx"

    page.source_model._rows[0]["up_id"] = "12345"

    index_up = page.paged_proxy.index(0, 2)
    page._on_table_clicked(index_up)
    assert opened_url == "https://space.bilibili.com/12345"
