from app.repositories import collections as collections_repo
from app.repositories import core as legacy_db
from app.repositories import following as following_repo
from app.repositories import history as history_repo
from app.repositories import stats as stats_repo
from app.repositories import videos as videos_repo
import database


def _to_dicts(rows):
    return [dict(row) for row in rows]


def test_query_parity_collections_and_collection_detail(seeded_fixture_db):
    with database.get_connection(str(seeded_fixture_db)) as conn:
        assert collections_repo.get_all_collections(conn) == _to_dicts(
            legacy_db.get_all_collections(conn)
        )
        assert _to_dicts(database.get_all_collections(conn)) == _to_dicts(
            legacy_db.get_all_collections(conn)
        )

        assert videos_repo.get_videos_in_collection(
            conn, 101, include_unfav=True
        ) == _to_dicts(legacy_db.get_videos_in_collection(conn, 101, include_unfav=True))
        assert videos_repo.get_videos_in_collection(
            conn, 202, include_unfav=False
        ) == _to_dicts(legacy_db.get_videos_in_collection(conn, 202, include_unfav=False))

        assert _to_dicts(
            database.get_videos_in_collection(conn, 202, include_unfav=True)
        ) == _to_dicts(legacy_db.get_videos_in_collection(conn, 202, include_unfav=True))


def test_query_parity_history_search_following_and_stats(seeded_fixture_db):
    with database.get_connection(str(seeded_fixture_db)) as conn:
        assert history_repo.get_video_history(conn, "BVTEST003") == legacy_db.get_video_history(
            conn, "BVTEST003"
        )
        assert database.get_video_history(conn, "BVTEST003") == legacy_db.get_video_history(
            conn, "BVTEST003"
        )

        assert videos_repo.get_all_videos_index(conn) == legacy_db.get_all_videos_index(conn)
        assert database.get_all_videos_index(conn) == legacy_db.get_all_videos_index(conn)

        assert following_repo.get_all_following_ups(conn) == _to_dicts(
            legacy_db.get_all_following_ups(conn)
        )
        assert _to_dicts(database.get_all_following_ups(conn)) == _to_dicts(
            legacy_db.get_all_following_ups(conn)
        )

        assert stats_repo.get_stats(conn) == legacy_db.get_stats(conn)
        assert database.get_stats(conn) == legacy_db.get_stats(conn)
