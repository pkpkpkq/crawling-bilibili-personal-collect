from app.repositories import stats


def test_stats_parity(monkeypatch):
    class MockConn:
        def execute(self, *args, **kwargs):
            pass

    mock_stats_data = {
        "total_videos": 10,
        "total_collections": 2,
        "total_ups": 3,
        "invalid_videos": 1,
        "following_ups": 2,
        "collection_counts": [{"name": "A", "count": 5}],
        "top_ups": [{"name": "UP A", "mid": 1, "count": 10}],
        "monthly_trend": [{"month": "2023-01", "count": 5}],
        "recent_invalid": [
            {"title": "Inv", "bv_id": "BV1", "up_name": "UP A", "collection": "C"}
        ],
        "recent_unfav": [
            {
                "title": "Unf",
                "bv_id": "BV2",
                "up_name": "UP B",
                "collection": "C",
                "unfav_time": "T",
            }
        ],
        "duration_distribution": {
            "<1分钟": 1,
            "1-5分钟": 2,
            "5-10分钟": 3,
            "10-30分钟": 4,
            "30-60分钟": 0,
            ">1小时": 0,
        },
        "crawl_history": [],
    }

    monkeypatch.setattr(
        "app.repositories.stats.get_stats", lambda conn: mock_stats_data
    )

    data = stats.get_stats(MockConn())

    expected_keys = [
        "total_videos",
        "total_collections",
        "total_ups",
        "following_ups",
        "invalid_videos",
        "collection_counts",
        "top_ups",
        "monthly_trend",
        "recent_invalid",
        "recent_unfav",
        "duration_distribution",
        "crawl_history",
    ]
    for key in expected_keys:
        assert key in data
