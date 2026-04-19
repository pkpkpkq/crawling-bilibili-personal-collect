import pytest
from PySide6.QtCore import Qt, QDate
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
        page.paged_proxy.index(0, 1), Qt.ItemDataRole.DisplayRole
    )
    assert first_row_bv == "BV2def"  # 2000 vs 1000

    page.sort_combo.setCurrentIndex(page.sort_combo.findData("duration_desc"))
    first_row_bv = page.paged_proxy.data(
        page.paged_proxy.index(0, 1), Qt.ItemDataRole.DisplayRole
    )
    assert first_row_bv == "BV2def"  # 1200 vs 600


def test_collection_page_history_expansion(qtbot, sample_rows):
    cache = CacheService()
    page = CollectionPage(cache_service=cache)
    qtbot.addWidget(page)

    # Add history
    sample_rows[0]["history"] = [
        {"action": "add", "time": "2023-01-01", "collection_name": "Dev"}
    ]

    page.load_data(1, "Dev", sample_rows)

    # Default is collapsed
    assert page._expanded_row == -1

    # Click row 0
    idx = page.paged_proxy.index(0, 0)
    page.table.clicked.emit(idx)

    # Verify expanded
    assert page._expanded_row == 0
    assert page._expanded_widget is not None
    assert page.table.rowHeight(0) == 200

    # Click again to collapse
    page.table.clicked.emit(idx)
    assert page._expanded_row == -1
    assert page._expanded_widget is None
