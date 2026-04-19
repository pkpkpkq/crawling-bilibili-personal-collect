from database import (
    get_all_collections,
    get_all_following_ups,
    get_all_videos_index,
    get_connection,
    get_stats,
    get_video_history,
)


REQUIRED_MIN_ROWS = {
    "collections": 2,
    "videos": 3,
    "video_collection": 4,
    "following_ups": 2,
    "crawl_history": 2,
}


def _count_rows(conn, table_name):
    return conn.execute(f"SELECT COUNT(*) AS c FROM {table_name}").fetchone()["c"]


def test_seed_guard_required_categories_present(seeded_fixture_db):
    with get_connection(str(seeded_fixture_db)) as conn:
        for table_name, expected_min in REQUIRED_MIN_ROWS.items():
            actual = _count_rows(conn, table_name)
            assert actual >= expected_min, (
                f"Seed guard failed for {table_name}: expected >= {expected_min}, got {actual}"
            )


def test_seed_guard_history_has_add_and_remove_events(seeded_fixture_db):
    with get_connection(str(seeded_fixture_db)) as conn:
        history = get_video_history(conn, "BVTEST003")

    event_types = {event["type"] for event in history}
    assert "add" in event_types
    assert "remove" in event_types


def test_seed_guard_repository_queries_have_data(seeded_fixture_db):
    with get_connection(str(seeded_fixture_db)) as conn:
        assert get_all_collections(conn)
        assert get_all_following_ups(conn)

        index = get_all_videos_index(conn)
        assert "BVTEST002" in index

        stats = get_stats(conn)
        for key in (
            "total_videos",
            "total_collections",
            "total_ups",
            "monthly_trend",
            "duration_distribution",
            "crawl_history",
        ):
            assert key in stats

        assert stats["crawl_history"]
