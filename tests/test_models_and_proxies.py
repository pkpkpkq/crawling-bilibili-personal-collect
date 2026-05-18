from datetime import date

from app.models import (
    CollectionFilterProxyModel,
    CollectionRowRole,
    CollectionRowsModel,
    GlobalSearchFilterProxyModel,
    GlobalSearchRowRole,
    GlobalSearchRowsModel,
    UpListFilterProxyModel,
    UpListRowRole,
    UpListRowsModel,
)


def _collection_rows():
    return [
        {
            "title": "Alpha One",
            "bv_id": "BV001",
            "up_name": "UP Alpha",
            "fav_time": "2024-01-01 08:00:00",
            "publish_time": "2023-12-10 10:00:00",
            "play_count": 100,
            "collect_count": 15,
            "danmaku_count": 3,
            "duration": "00:01:00",
            "is_invalid": 0,
            "is_active": 1,
            "collection_name": "Tech Picks",
            "latest_collection": "Tech Picks",
            "history": [{"type": "add", "collection": "Tech Picks", "time": "2024-01-01 08:00:00"}],
            "cover_path": "cache/covers/BV001.jpg",
        },
        {
            "title": "Bravo Current",
            "bv_id": "BV002",
            "up_name": "UP Bravo",
            "fav_time": "2024-02-10 09:00:00",
            "publish_time": "2024-02-01 09:30:00",
            "play_count": 500,
            "collect_count": 300,
            "danmaku_count": 40,
            "duration": "00:10:30",
            "is_invalid": 0,
            "is_active": 1,
            "collection_name": "Tech Picks",
            "latest_collection": "Tech Picks",
            "history": [{"type": "add", "collection": "Tech Picks", "time": "2024-02-10 09:00:00"}],
            "cover_path": "cache/covers/BV002.jpg",
        },
        {
            "title": "Charlie Invalid",
            "bv_id": "BV003",
            "up_name": "UP Bravo",
            "fav_time": "2024-03-01 10:00:00",
            "publish_time": "2024-02-28 20:00:00",
            "play_count": 50,
            "collect_count": 5,
            "danmaku_count": 1,
            "duration": "00:00:45",
            "is_invalid": 1,
            "is_active": 1,
            "collection_name": "Tech Picks",
            "latest_collection": "Tech Picks",
            "history": [{"type": "add", "collection": "Tech Picks", "time": "2024-03-01 10:00:00"}],
            "cover_path": "cache/covers/BV003.jpg",
        },
        {
            "title": "Delta Moved",
            "bv_id": "BV004",
            "up_name": "UP Delta",
            "fav_time": "2024-01-15 11:00:00",
            "publish_time": "2024-01-05 10:00:00",
            "play_count": 200,
            "collect_count": 20,
            "danmaku_count": 10,
            "duration": "01:02:03",
            "is_invalid": 0,
            "is_active": 1,
            "collection_name": "Tech Picks",
            "latest_collection": "Music Box",
            "history": [{"type": "add", "collection": "Tech Picks", "time": "2024-01-15 11:00:00"}],
            "cover_path": "cache/covers/BV004.jpg",
        },
    ]


def _global_index_rows():
    return {
        "BV001": {
            "bvid": "BV001",
            "info": {
                "title": "Alpha One",
                "up_name": "UP Alpha",
                "up_id": 11,
                "is_invalid": False,
                "is_unfavorited": False,
                "cover_path": "cache/covers/BV001.jpg",
                "up_face_path": "cache/up_faces/11.jpg",
            },
            "history": [],
            "latest_collection": "Tech Picks",
            "latest_fav_time": "2024-01-01 08:00:00",
        },
        "BV002": {
            "bvid": "BV002",
            "info": {
                "title": "Beta Search",
                "up_name": "UP Beta",
                "up_id": 22,
                "is_invalid": False,
                "is_unfavorited": False,
                "cover_path": "cache/covers/BV002.jpg",
                "up_face_path": "cache/up_faces/22.jpg",
            },
            "history": [],
            "latest_collection": "Music Box",
            "latest_fav_time": "2024-03-01 10:00:00",
        },
        "BV003": {
            "bvid": "BV003",
            "info": {
                "title": "Gamma Old",
                "up_name": "UP Gamma",
                "up_id": 33,
                "is_invalid": True,
                "is_unfavorited": True,
                "cover_path": "cache/covers/BV003.jpg",
                "up_face_path": "cache/up_faces/33.jpg",
            },
            "history": [],
            "latest_collection": "Archive",
            "latest_fav_time": "2023-10-01 00:00:00",
        },
    }


def _up_rows():
    return [
        {"mid": 1002, "name": "UP Zebra", "face_url": "https://example.invalid/2.jpg"},
        {"mid": 1001, "name": "UP Alpha", "face_url": "https://example.invalid/1.jpg"},
        {"mid": 1003, "name": "UP 音乐", "face_url": "https://example.invalid/3.jpg"},
    ]


def test_collection_rows_model_exposes_roles_and_display_data():
    rows = _collection_rows()
    model = CollectionRowsModel(rows)

    assert model.rowCount() == len(rows)
    assert model.columnCount() == 10

    title_index = model.index(0, 1)
    assert model.data(title_index) == "Alpha One"
    assert model.data(model.index(0, 0), int(CollectionRowRole.COVER_PATH)) == "cache/covers/BV001.jpg"
    assert model.data(title_index, int(CollectionRowRole.BV_ID)) == "BV001"
    assert model.data(title_index, int(CollectionRowRole.IS_CURRENT)) is True
    assert model.data(model.index(2, 1), int(CollectionRowRole.IS_CURRENT)) is False


def test_collection_filter_proxy_search_current_toggle_and_date_ranges(qapp):
    model = CollectionRowsModel(_collection_rows())
    proxy = CollectionFilterProxyModel()
    proxy.setSourceModel(model)

    assert proxy.rowCount() == 4

    proxy.setSearchText("bravo")
    assert proxy.rowCount() == 2

    proxy.setShowCurrentOnly(True)
    # BV002 is current; BV003 is invalid.
    assert proxy.rowCount() == 1
    index = proxy.index(0, 0)
    assert proxy.data(index, int(CollectionRowRole.BV_ID)) == "BV002"

    proxy.setSearchText("")
    proxy.setShowCurrentOnly(False)
    proxy.setFavoriteDateRange(date(2024, 2, 1), date(2024, 3, 1))
    assert proxy.rowCount() == 2

    proxy.setFavoriteDateRange(None, None)
    proxy.setPublishDateRange("2024-02-01", "2024-12-31")
    assert proxy.rowCount() == 2


def test_collection_filter_proxy_sort_keys_match_legacy_behavior(qapp):
    model = CollectionRowsModel(_collection_rows())
    proxy = CollectionFilterProxyModel()
    proxy.setSourceModel(model)

    proxy.setSortKey("fav_desc")
    assert [proxy.data(proxy.index(i, 0), int(CollectionRowRole.BV_ID)) for i in range(proxy.rowCount())] == [
        "BV003",
        "BV002",
        "BV004",
        "BV001",
    ]

    proxy.setSortKey("fav_asc")
    assert [proxy.data(proxy.index(i, 0), int(CollectionRowRole.BV_ID)) for i in range(proxy.rowCount())] == [
        "BV001",
        "BV004",
        "BV002",
        "BV003",
    ]

    proxy.setSortKey("play_desc")
    assert [proxy.data(proxy.index(i, 0), int(CollectionRowRole.BV_ID)) for i in range(proxy.rowCount())] == [
        "BV002",
        "BV004",
        "BV001",
        "BV003",
    ]

    proxy.setSortKey("duration_desc")
    assert [proxy.data(proxy.index(i, 0), int(CollectionRowRole.BV_ID)) for i in range(proxy.rowCount())] == [
        "BV004",
        "BV002",
        "BV001",
        "BV003",
    ]


def test_global_search_model_and_proxy_keyword_and_latest_sort(qapp):
    model = GlobalSearchRowsModel(_global_index_rows())
    proxy = GlobalSearchFilterProxyModel()
    proxy.setSourceModel(model)

    # Default ordering is latest_fav_time desc.
    assert [proxy.data(proxy.index(i, 0), int(GlobalSearchRowRole.BV_ID)) for i in range(proxy.rowCount())] == [
        "BV002",
        "BV001",
        "BV003",
    ]

    proxy.setSearchText("beta")
    assert proxy.rowCount() == 1
    assert proxy.data(proxy.index(0, 0), int(GlobalSearchRowRole.BV_ID)) == "BV002"

    proxy.setSearchText("up")
    assert proxy.rowCount() == 3


def test_up_list_model_and_proxy_filtering(qapp):
    model = UpListRowsModel(_up_rows())
    proxy = UpListFilterProxyModel()
    proxy.setSourceModel(model)

    # Alphabetical by casefolded display name.
    assert [proxy.data(proxy.index(i, 0), int(UpListRowRole.NAME)) for i in range(proxy.rowCount())] == [
        "UP Alpha",
        "UP Zebra",
        "UP 音乐",
    ]

    proxy.setSearchText("alpha")
    assert proxy.rowCount() == 1
    assert proxy.data(proxy.index(0, 0), int(UpListRowRole.MID)) == 1001
