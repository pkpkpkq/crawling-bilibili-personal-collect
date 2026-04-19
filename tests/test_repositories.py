import json

from app.repositories import (
    collections as collections_repo,
    history as history_repo,
    migrations as migrations_repo,
    stats as stats_repo,
    videos as videos_repo,
)
from database import get_connection, get_db_path


def test_collections_repository_returns_stable_dict_rows(seeded_fixture_db):
    with get_connection(str(seeded_fixture_db)) as conn:
        rows = collections_repo.get_all_collections(conn)

    assert rows
    assert all(isinstance(row, dict) for row in rows)
    assert [row["name"] for row in rows] == sorted(row["name"] for row in rows)


def test_videos_repository_preserves_include_unfav_contract(seeded_fixture_db):
    with get_connection(str(seeded_fixture_db)) as conn:
        with_unfav = videos_repo.get_videos_in_collection(conn, 202, include_unfav=True)
        active_only = videos_repo.get_videos_in_collection(conn, 202, include_unfav=False)

    assert any(row["bv_id"] == "BVTEST003" for row in with_unfav)
    assert all(row["is_active"] == 1 for row in active_only)
    assert {row["bv_id"] for row in active_only} == {"BVTEST002"}


def test_history_repository_returns_add_remove_contract(seeded_fixture_db):
    with get_connection(str(seeded_fixture_db)) as conn:
        events = history_repo.get_video_history(conn, "BVTEST003")

    assert events
    assert all(set(event.keys()) == {"type", "collection", "time"} for event in events)
    assert {event["type"] for event in events} == {"add", "remove"}


def test_video_index_repository_structure(seeded_fixture_db):
    with get_connection(str(seeded_fixture_db)) as conn:
        index = videos_repo.get_all_videos_index(conn)

    assert "BVTEST002" in index
    row = index["BVTEST002"]
    assert set(row.keys()) == {
        "bvid",
        "info",
        "history",
        "latest_collection",
        "latest_fav_time",
    }
    assert set(row["info"].keys()) == {
        "title",
        "up_name",
        "up_id",
        "is_invalid",
        "is_unfavorited",
        "cover_path",
        "up_face_path",
    }


def test_stats_repository_contract_has_dashboard_keys(seeded_fixture_db):
    with get_connection(str(seeded_fixture_db)) as conn:
        stats = stats_repo.get_stats(conn)

    for key in (
        "total_videos",
        "total_collections",
        "total_ups",
        "invalid_videos",
        "following_ups",
        "collection_counts",
        "top_ups",
        "monthly_trend",
        "recent_invalid",
        "recent_unfav",
        "duration_distribution",
        "crawl_history",
    ):
        assert key in stats


def test_json_migration_helper_preserves_contract(tmp_path):
    json_dir = tmp_path / "json"
    json_dir.mkdir(parents=True, exist_ok=True)

    video_payload = {
        "id": 42,
        "BV": "BVJSON001",
        "是否失效": False,
        "up主": {"ID": 100, "昵称": "JsonUP", "头像": "https://example.invalid/up.jpg"},
        "视频信息": {
            "标题": "JSON Video",
            "封面": "https://example.invalid/BVJSON001.jpg",
            "简介": "from json",
            "时长": "00:01:00",
        },
        "观众数据": {"播放量": 1, "收藏量": 2, "弹幕数量": 3},
        "三个时间": {
            "上传时间": "2024-01-01 00:00:00",
            "发布时间": "2024-01-01 00:00:00",
            "收藏时间": "2024-02-01 00:00:00",
        },
    }

    (json_dir / "Json收藏夹.json").write_text(
        json.dumps({"42": video_payload}, ensure_ascii=False),
        encoding="utf-8",
    )
    (json_dir / "关注UP列表.json").write_text(
        json.dumps(
            [{"ID": 100, "昵称": "JsonUP", "头像": "https://example.invalid/up.jpg"}],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    db_path = get_db_path(str(tmp_path))
    migrations_repo.migrate_from_json(str(json_dir), db_path)

    with get_connection(db_path) as conn:
        assert conn.execute("SELECT COUNT(*) AS c FROM collections").fetchone()["c"] == 1
        assert conn.execute("SELECT COUNT(*) AS c FROM videos").fetchone()["c"] == 1
        assert conn.execute("SELECT COUNT(*) AS c FROM video_collection").fetchone()["c"] == 1
        assert conn.execute("SELECT COUNT(*) AS c FROM following_ups").fetchone()["c"] == 1
