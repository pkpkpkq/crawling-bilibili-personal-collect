from database import get_connection, get_db_path, init_db


EXPECTED_SCHEMA = {
    "collections": ["id", "name", "media_count", "api_mtime", "last_crawl_time"],
    "ups": ["mid", "name", "face_url"],
    "videos": [
        "bv_id",
        "av_id",
        "title",
        "cover_url",
        "intro",
        "duration",
        "up_mid",
        "play_count",
        "collect_count",
        "danmaku_count",
        "upload_time",
        "publish_time",
        "is_invalid",
    ],
    "video_collection": [
        "id",
        "bv_id",
        "collection_id",
        "fav_time",
        "unfav_time",
        "is_active",
    ],
    "following_ups": ["mid", "name", "face_url"],
    "crawl_history": [
        "id",
        "crawl_time",
        "duration_seconds",
        "total_videos",
        "new_videos",
        "invalid_videos",
        "unfav_videos",
        "status",
    ],
}

EXPECTED_INDEXES = {
    "idx_vc_bv",
    "idx_vc_coll",
    "idx_videos_up",
    "idx_vc_fav_time",
}


def _table_columns(conn, table_name):
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [row["name"] for row in rows]


def test_repository_schema_guard_exact_tables_and_columns(tmp_path):
    db_path = get_db_path(str(tmp_path))
    init_db(db_path)

    with get_connection(db_path) as conn:
        tables = {
            row["name"]
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            """
            ).fetchall()
        }
        assert tables == set(EXPECTED_SCHEMA.keys())

        for table_name, expected_columns in EXPECTED_SCHEMA.items():
            assert _table_columns(conn, table_name) == expected_columns


def test_repository_schema_guard_required_indexes_present(tmp_path):
    db_path = get_db_path(str(tmp_path))
    init_db(db_path)

    with get_connection(db_path) as conn:
        index_names = {
            row["name"]
            for row in conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'index' AND name NOT LIKE 'sqlite_autoindex%'
            """
            ).fetchall()
        }

    for index_name in EXPECTED_INDEXES:
        assert index_name in index_names
