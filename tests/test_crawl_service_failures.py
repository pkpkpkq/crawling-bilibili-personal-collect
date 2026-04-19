from app.repositories.connection import get_connection
from app.services.crawl_service import CrawlService


def test_run_headless_crawl_records_failed_history_when_favorites_unavailable(
    tmp_path, monkeypatch
):
    db_path = str(tmp_path / "bilibili_data.db")
    service = CrawlService(sleep_func=lambda _: None)

    monkeypatch.setattr(service, "verify_cookie", lambda headers: True)
    monkeypatch.setattr(service, "get_favorite_id_list", lambda uid, headers: None)

    sync_called = {"value": False}

    def fake_sync_images(*args, **kwargs):
        sync_called["value"] = True
        return {"success": 0, "total": 0}

    monkeypatch.setattr(service, "sync_images", fake_sync_images)

    result = service.run_headless_crawl(
        uid="uid-1", cookie="SESSDATA=aaa", settings={}, db_path=db_path
    )

    assert result.success is False
    assert sync_called["value"] is False
    assert result.stats == {"new": 0, "invalid": 0, "unfav": 0, "total": 0}

    with get_connection(db_path) as conn:
        rows = conn.execute(
            "SELECT status, total_videos, new_videos, invalid_videos, unfav_videos FROM crawl_history"
        ).fetchall()

    assert len(rows) == 1
    row = rows[0]
    assert row["status"] == "failed"
    assert row["total_videos"] == 0
    assert row["new_videos"] == 0
    assert row["invalid_videos"] == 0
    assert row["unfav_videos"] == 0


def test_run_headless_crawl_records_failed_history_when_image_sync_raises(
    tmp_path, monkeypatch
):
    db_path = str(tmp_path / "bilibili_data.db")
    service = CrawlService(sleep_func=lambda _: None)

    monkeypatch.setattr(service, "verify_cookie", lambda headers: True)
    monkeypatch.setattr(
        service,
        "get_favorite_id_list",
        lambda uid, headers: [
            {"id": 1001, "title": "A", "media_count": 1, "mtime": 1}
        ],
    )
    monkeypatch.setattr(service, "get_following_ups", lambda uid, headers: [])
    monkeypatch.setattr(
        service,
        "crawl_one_favorite",
        lambda *args, **kwargs: {
            "name": "A",
            "skipped": False,
            "new": 1,
            "invalid": 0,
            "unfav": 0,
        },
    )

    def raise_sync(*args, **kwargs):
        raise RuntimeError("sync boom")

    monkeypatch.setattr(service, "sync_images", raise_sync)

    result = service.run_headless_crawl(
        uid="uid-1", cookie="SESSDATA=aaa", settings={}, db_path=db_path
    )

    assert result.success is False
    assert "sync boom" in (result.error or "")
    assert result.stats == {"new": 0, "invalid": 0, "unfav": 0, "total": 0}

    with get_connection(db_path) as conn:
        statuses = [
            row["status"]
            for row in conn.execute("SELECT status FROM crawl_history ORDER BY id").fetchall()
        ]

    assert statuses == ["failed"]
