from app.repositories import collections as collections_repo
from app.repositories.connection import get_connection, init_db
from app.services.crawl_service import CrawlService


def test_run_headless_crawl_success_records_summary_following_and_history(
    tmp_path, monkeypatch
):
    db_path = str(tmp_path / "bilibili_data.db")
    perf_values = iter([10.0, 14.25])
    service = CrawlService(
        sleep_func=lambda _: None,
        perf_counter_func=lambda: next(perf_values),
    )

    monkeypatch.setattr(service, "verify_cookie", lambda headers: True)
    monkeypatch.setattr(
        service,
        "get_favorite_id_list",
        lambda uid, headers: [
            {"id": 1001, "title": "A", "media_count": 2, "mtime": 10},
            {"id": 1002, "title": "B", "media_count": 2, "mtime": 10},
        ],
    )
    monkeypatch.setattr(
        service,
        "get_following_ups",
        lambda uid, headers: [
            {
                "ID": 2001,
                "昵称": "UP-A",
                "头像": "https://example.invalid/up-a.jpg",
            }
        ],
    )

    def fake_crawl_one_favorite(fav_item, headers, db_path_arg, settings_arg):
        assert db_path_arg == db_path
        if fav_item["id"] == 1001:
            return {"name": "A", "skipped": False, "new": 2, "invalid": 1, "unfav": 0}
        return {"name": "B", "skipped": True, "new": 0, "invalid": 0, "unfav": 0}

    monkeypatch.setattr(service, "crawl_one_favorite", fake_crawl_one_favorite)

    sync_call = {}

    def fake_sync_images(db_path_arg, settings_arg, report_dir="html_report"):
        sync_call["db_path"] = db_path_arg
        sync_call["report_dir"] = report_dir
        return {"success": 0, "total": 0}

    monkeypatch.setattr(service, "sync_images", fake_sync_images)

    result = service.run_headless_crawl(
        uid="uid-1",
        cookie="COOKIE=abc",
        settings={"max_workers_crawl": 2},
        db_path=db_path,
        report_dir="headless-assets",
    )

    assert result.success is True
    assert result.duration_seconds == 4.25
    assert result.stats == {"new": 2, "invalid": 1, "unfav": 0, "total": 0}
    assert sync_call["db_path"] == db_path
    assert sync_call["report_dir"] == "headless-assets"

    with get_connection(db_path) as conn:
        history_row = conn.execute(
            "SELECT status, new_videos, invalid_videos, unfav_videos FROM crawl_history ORDER BY id DESC LIMIT 1"
        ).fetchone()
        following_count = conn.execute(
            "SELECT COUNT(*) AS c FROM following_ups"
        ).fetchone()["c"]

    assert history_row["status"] == "success"
    assert history_row["new_videos"] == 2
    assert history_row["invalid_videos"] == 1
    assert history_row["unfav_videos"] == 0
    assert following_count == 1


def test_crawl_one_favorite_skips_when_incremental_state_unchanged(
    tmp_path, monkeypatch
):
    db_path = str(tmp_path / "bilibili_data.db")
    init_db(db_path)

    with get_connection(db_path) as conn:
        collections_repo.upsert_collection(
            conn,
            coll_id=3001,
            name="Stable Collection",
            media_count=20,
            api_mtime=99,
        )

    service = CrawlService(sleep_func=lambda _: None)

    def should_not_fetch(*args, **kwargs):
        raise AssertionError("incremental skip should not fetch pages")

    monkeypatch.setattr(service, "get_one_favorite", should_not_fetch)

    result = service.crawl_one_favorite(
        fav_item={
            "id": 3001,
            "title": "Stable Collection",
            "media_count": 20,
            "mtime": 99,
        },
        headers={},
        db_path=db_path,
        settings={"enable_incremental": True},
    )

    assert result == {
        "name": "Stable Collection",
        "skipped": True,
        "new": 0,
        "invalid": 0,
        "unfav": 0,
    }
