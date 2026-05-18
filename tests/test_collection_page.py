from app.ui.pages.collection_page import CollectionPage
from app.services.cache_service import CacheService


def test_collection_page_initialization(qtbot):
    cache = CacheService()
    page = CollectionPage(cache_service=cache)
    qtbot.addWidget(page)

    assert page.title_label.text() == "收藏夹"
    assert page.page_stack.currentWidget() == page.list_page
    assert page.search_input.placeholderText() == "搜索 标题/BV号/UP主..."
    assert page.current_only_cb.text() == "仅显示当前有效视频"
    assert page.sort_combo.count() == 8


def test_collection_page_load_data(qtbot):
    cache = CacheService()
    page = CollectionPage(cache_service=cache)
    qtbot.addWidget(page)

    rows = [
        {
            "title": "Test Video",
            "bv_id": "BV1xx411c7m9",
            "up_name": "Test UP",
            "fav_time": 1600000000.0,
            "publish_time": 1500000000.0,
            "play_count": 100,
            "collect_count": 50,
            "danmaku_count": 10,
            "duration": 120,
            "is_active": True,
            "is_invalid": False,
            "collection_name": "My Favs",
            "latest_collection": "My Favs",
            "cover_path": "cache/covers/BV1xx411c7m9.jpg",
        }
    ]

    page.load_data(1, "My Favs", rows)
    assert page.title_label.text() == "收藏夹: My Favs"
    assert page.page_stack.currentWidget() == page.detail_page
    assert page.source_model.rowCount() == 1
    assert page.paged_proxy.rowCount() == 1
    assert page.source_model.columnCount() == 10
    assert page.source_model.data(page.source_model.index(0, 0)) == "cache/covers/BV1xx411c7m9.jpg"
    assert "1" in page.page_label.text()


def test_collection_page_back_to_list(qtbot):
    cache = CacheService()
    page = CollectionPage(cache_service=cache)
    qtbot.addWidget(page)

    page.load_data(1, "My Favs", [])
    page.back_btn.click()

    assert page.page_stack.currentWidget() == page.list_page
