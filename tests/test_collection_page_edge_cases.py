import pytest
from PySide6.QtCore import Qt, QDate
from app.ui.pages.collection_page import CollectionPage
from app.services.cache_service import CacheService


@pytest.fixture
def empty_cache():
    return CacheService()


def test_collection_page_empty_rows(qtbot, empty_cache):
    page = CollectionPage(cache_service=empty_cache)
    qtbot.addWidget(page)

    page.load_data(1, "Empty", [])

    assert page.paged_proxy.rowCount() == 0
    assert page.paged_proxy.pageCount() == 1
    assert "0" in page.page_label.text()
    assert not page.prev_btn.isEnabled()
    assert not page.next_btn.isEnabled()


def test_collection_page_null_history(qtbot, empty_cache):
    page = CollectionPage(cache_service=empty_cache)
    qtbot.addWidget(page)

    rows = [
        {
            "title": "A Video",
            "bv_id": "BV1",
            "up_name": "UP",
            "fav_time": 1000,
            "publish_time": 1000,
            "play_count": 0,
            "collect_count": 0,
            "danmaku_count": 0,
            "duration": 0,
            "is_active": True,
            "is_invalid": False,
            "collection_name": "C",
            "latest_collection": "C",
        }
    ]

    page.load_data(1, "C", rows)

    idx = page.paged_proxy.index(0, 0)
    page.table.clicked.emit(idx)

    assert page._expanded_widget is not None
    assert page._expanded_widget.layout().count() >= 2
    assert page._expanded_widget.layout().itemAt(1).widget().text() == "暂无历史记录"


def test_collection_page_invalid_date_clearing(qtbot, empty_cache):
    page = CollectionPage(cache_service=empty_cache)
    qtbot.addWidget(page)

    page.fav_start.setDate(QDate(2023, 1, 1))
    assert page.fav_start.date() != page.fav_start.minimumDate()

    page.clear_dates_btn.click()

    assert page.fav_start.date() == page.fav_start.minimumDate()
    assert page.fav_end.date() == page.fav_start.minimumDate()
