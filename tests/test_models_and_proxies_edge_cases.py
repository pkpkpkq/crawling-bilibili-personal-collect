from app.models import (
    CollectionFilterProxyModel,
    CollectionRowRole,
    CollectionRowsModel,
    GlobalSearchFilterProxyModel,
    GlobalSearchRowRole,
    GlobalSearchRowsModel,
)


def _collection_edge_rows():
    return [
        {
            "title": "Bad Date",
            "bv_id": "BV_BAD_1",
            "up_name": "UP Broken",
            "fav_time": "not-a-date",
            "publish_time": "2024-01-01 00:00:00",
            "play_count": "NaN",
            "collect_count": None,
            "danmaku_count": "",
            "duration": "broken",
            "is_invalid": 0,
            "is_active": 1,
            "collection_name": "Tech Picks",
            "latest_collection": "Tech Picks",
            "history": "not-a-list",
        },
        {
            "title": "Missing History",
            "bv_id": "BV_BAD_2",
            "up_name": "UP Missing",
            "fav_time": "2024-01-02 00:00:00",
            "publish_time": "bad-date",
            "play_count": 10,
            "collect_count": 1,
            "danmaku_count": 1,
            "duration": "00:00:05",
            "is_invalid": 0,
            "is_active": 1,
            "collection_name": "Tech Picks",
            "latest_collection": "Tech Picks",
        },
    ]


def _global_edge_rows():
    return {
        "BV_EDGE": {
            "bvid": "BV_EDGE",
            "info": {
                "title": "Edge Case",
                "up_name": "UP Edge",
                "up_id": 1,
                "is_invalid": False,
                "is_unfavorited": False,
                "cover_path": "cache/covers/BV_EDGE.jpg",
                "up_face_path": "cache/up_faces/1.jpg",
            },
            "history": None,
            "latest_collection": "N/A",
            "latest_fav_time": "not-a-date",
        },
        "BV_EDGE_2": {
            "bvid": "BV_EDGE_2",
            "info": {
                "title": "Another Edge",
                "up_name": "UP Another",
                "up_id": 2,
                "is_invalid": False,
                "is_unfavorited": False,
                "cover_path": "cache/covers/BV_EDGE_2.jpg",
                "up_face_path": "cache/up_faces/2.jpg",
            },
            "history": [],
            "latest_collection": "N/A",
            "latest_fav_time": "2024-01-01 00:00:00",
        },
    }


def test_collection_proxy_handles_malformed_dates_and_empty_results(qapp):
    source = CollectionRowsModel(_collection_edge_rows())
    proxy = CollectionFilterProxyModel()
    proxy.setSourceModel(source)

    proxy.setFavoriteDateRange("2024-01-01", "2024-01-31")
    # First row has malformed fav_time and should be filtered out.
    assert proxy.rowCount() == 1

    proxy.setSearchText("no-match-text")
    assert proxy.rowCount() == 0


def test_collection_model_history_role_tolerates_missing_or_invalid_history():
    source = CollectionRowsModel(_collection_edge_rows())
    assert source.data(source.index(0, 0), int(CollectionRowRole.HISTORY)) == []
    assert source.data(source.index(1, 0), int(CollectionRowRole.HISTORY)) == []


def test_global_search_proxy_prefers_valid_latest_favorite_dates(qapp):
    source = GlobalSearchRowsModel(_global_edge_rows())
    proxy = GlobalSearchFilterProxyModel()
    proxy.setSourceModel(source)

    assert proxy.rowCount() == 2
    # Valid dated row should appear before malformed date row.
    assert proxy.data(proxy.index(0, 0), int(GlobalSearchRowRole.BV_ID)) == "BV_EDGE_2"
    assert proxy.data(proxy.index(1, 0), int(GlobalSearchRowRole.BV_ID)) == "BV_EDGE"


def test_global_search_proxy_empty_query_and_missing_history_do_not_crash(qapp):
    source = GlobalSearchRowsModel(_global_edge_rows())
    proxy = GlobalSearchFilterProxyModel()
    proxy.setSourceModel(source)

    proxy.setSearchText("")
    assert proxy.rowCount() == 2

    proxy.setSearchText("edge")
    assert proxy.rowCount() == 2

    proxy.setSearchText("missing")
    assert proxy.rowCount() == 0
