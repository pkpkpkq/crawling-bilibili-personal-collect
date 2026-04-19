from pathlib import Path

from database import get_connection, get_db_path


def test_fixture_database_uses_temp_sqlite_path(seeded_fixture_db, tmp_path):
    expected = Path(get_db_path(str(tmp_path)))
    assert seeded_fixture_db == expected
    assert seeded_fixture_db.exists()
    assert tmp_path in seeded_fixture_db.parents


def test_fixture_contains_representative_seed_entities(seeded_fixture_summary):
    assert seeded_fixture_summary["collections"] >= 2
    assert seeded_fixture_summary["videos"] >= 3
    assert seeded_fixture_summary["video_collection"] >= 4
    assert seeded_fixture_summary["following_ups"] >= 2
    assert seeded_fixture_summary["crawl_history"] >= 2


def test_fixture_contains_invalid_and_unfavorited_examples(seeded_fixture_db):
    with get_connection(str(seeded_fixture_db)) as conn:
        invalid_count = conn.execute(
            "SELECT COUNT(*) AS c FROM videos WHERE is_invalid = 1"
        ).fetchone()["c"]
        unfav_count = conn.execute(
            "SELECT COUNT(*) AS c FROM video_collection WHERE is_active = 0"
        ).fetchone()["c"]

    assert invalid_count >= 1
    assert unfav_count >= 1
