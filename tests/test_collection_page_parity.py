import pytest
from PySide6.QtCore import Qt
from app.ui.pages.collection_page import CollectionPage
from app.services.cache_service import CacheService


@pytest.fixture
def sample_rows():
    return [
        {
            "title": "A React Tutorial",
            "bv_id": "BV1abc",
            "up_name": "Web Dev",
            "fav_time": 1700000000.0,
            "publish_time": 1690000000.0,
            "play_count": 1000,
            "collect_count": 500,
            "danmaku_count": 100,
            "duration": 600,
            "is_active": True,
            "is_invalid": False,
            "collection_name": "Dev",
            "latest_collection": "Dev",
        },
        {
            "title": "Python Basics",
            "bv_id": "BV2def",
            "up_name": "Py Master",
            "fav_time": 1600000000.0,
            "publish_time": 1590000000.0,
            "play_count": 2000,
            "collect_count": 300,
            "danmaku_count": 50,
            "duration": 1200,
            "is_active": False,
            "is_invalid": True,
            "collection_name": "Dev",
            "latest_collection": "Archived",
        },
    ]


def test_collection_page_search(qtbot, sample_rows):
    cache = CacheService()
    page = CollectionPage(cache_service=cache)
    qtbot.addWidget(page)

    page.load_data(1, "Dev", sample_rows)
    assert page.page_stack.currentWidget() == page.detail_page
    assert page.paged_proxy.rowCount() == 2

    page.search_input.setText("react")
    assert page.paged_proxy.rowCount() == 1

    page.search_input.setText("master")
    assert page.paged_proxy.rowCount() == 1

    page.search_input.setText("bv1")
    assert page.paged_proxy.rowCount() == 1

    page.search_input.clear()
    assert page.paged_proxy.rowCount() == 2


def test_collection_page_current_only(qtbot, sample_rows):
    cache = CacheService()
    page = CollectionPage(cache_service=cache)
    qtbot.addWidget(page)

    page.load_data(1, "Dev", sample_rows)
    assert page.paged_proxy.rowCount() == 2

    page.current_only_cb.setChecked(True)
    assert page.paged_proxy.rowCount() == 1

    page.current_only_cb.setChecked(False)
    assert page.paged_proxy.rowCount() == 2


def test_collection_page_sorting(qtbot, sample_rows):
    cache = CacheService()
    page = CollectionPage(cache_service=cache)
    qtbot.addWidget(page)

    page.load_data(1, "Dev", sample_rows)

    page.sort_combo.setCurrentIndex(page.sort_combo.findData("play_desc"))
    first_row_bv = page.paged_proxy.data(
        page.paged_proxy.index(0, 2), Qt.ItemDataRole.DisplayRole
    )
    assert first_row_bv == "BV2def"

    page.sort_combo.setCurrentIndex(page.sort_combo.findData("duration_desc"))
    first_row_bv = page.paged_proxy.data(
        page.paged_proxy.index(0, 2), Qt.ItemDataRole.DisplayRole
    )
    assert first_row_bv == "BV2def"


def test_collection_page_history_expansion(qtbot, sample_rows):
    cache = CacheService()
    page = CollectionPage(cache_service=cache)
    qtbot.addWidget(page)

    sample_rows[0]["history"] = [
        {"action": "add", "time": "2023-01-01", "collection_name": "Dev"}
    ]

    page.load_data(1, "Dev", sample_rows)

    idx = page.paged_proxy.index(0, 0)
    page.delegate.toggleExpanded(idx)

    assert page.delegate._is_expanded(idx)
    assert "[2023-01-01] 添加 | 收藏夹: Dev" in page.delegate._expanded_content(idx)

    page.delegate.toggleExpanded(idx)
    assert not page.delegate._is_expanded(idx)


def test_collection_page_emits_selection_signal(qtbot):
    cache = CacheService()
    page = CollectionPage(cache_service=cache)
    qtbot.addWidget(page)

    page.set_collection_list([{"id": 3612401255, "name": "My List"}])
    with qtbot.waitSignal(page.collection_selected, timeout=1000) as blocker:
        page.collection_list.itemClicked.emit(page.collection_list.item(0))

    assert blocker.args == [3612401255, "My List"]

def test_collection_page_history_supports_repository_shape(qtbot, sample_rows):
    cache = CacheService()
    page = CollectionPage(cache_service=cache)
    qtbot.addWidget(page)

    sample_rows[0]["history"] = [
        {"type": "add", "collection": "Dev", "time": "2023-01-01 10:00:00"}
    ]

    page.load_data(1, "Dev", sample_rows)
    idx = page.paged_proxy.index(0, 0)
    page.delegate.toggleExpanded(idx)

    assert "[2023-01-01 10:00:00] 添加 | 收藏夹: Dev" in page.delegate._expanded_content(idx)


def test_collection_page_history_sorts_latest_first(qtbot, sample_rows):
    cache = CacheService()
    page = CollectionPage(cache_service=cache)
    qtbot.addWidget(page)

    sample_rows[0]["history"] = [
        {"type": "add", "collection": "Dev", "time": "2023-01-01 10:00:00"},
        {"type": "remove", "collection": "Dev", "time": "2023-01-02 11:00:00"},
    ]

    page.load_data(1, "Dev", sample_rows)
    idx = page.paged_proxy.index(0, 0)
    page.delegate.toggleExpanded(idx)

    lines = page.delegate._expanded_content(idx).splitlines()
    assert lines[1] == "[2023-01-02 11:00:00] 移除 | 收藏夹: Dev"
    assert lines[2] == "[2023-01-01 10:00:00] 添加 | 收藏夹: Dev"
