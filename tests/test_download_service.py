import json
from types import SimpleNamespace

from app.repositories.connection import get_connection, get_db_path, init_db
from app.repositories.core import add_video_to_collection, upsert_collection, upsert_video
from app.services.download_service import DownloadService


def _build_video_payload(*, av_id, bv_id, title, up_mid, invalid, fav_time):
    return {
        "id": av_id,
        "BV": bv_id,
        "是否失效": invalid,
        "up主": {
            "ID": up_mid,
            "昵称": f"UP-{up_mid}",
            "头像": f"https://example.invalid/{up_mid}.jpg",
        },
        "视频信息": {
            "标题": title,
            "封面": f"https://example.invalid/{bv_id}.jpg",
            "简介": "intro",
            "时长": "00:01:00",
        },
        "观众数据": {"播放量": 1, "收藏量": 1, "弹幕数量": 1},
        "三个时间": {
            "上传时间": "2024-01-01 00:00:00",
            "发布时间": "2024-01-01 00:00:00",
            "收藏时间": fav_time,
        },
    }


def _seed_download_fixture(db_path):
    with get_connection(db_path) as conn:
        upsert_collection(conn, 501, "Downloader Collection", media_count=3, api_mtime=1)

        upsert_video(
            conn,
            _build_video_payload(
                av_id=111,
                bv_id="BVACTIVE01",
                title="Active Video 1",
                up_mid=9001,
                invalid=False,
                fav_time="2024-01-10 00:00:00",
            ),
        )
        upsert_video(
            conn,
            _build_video_payload(
                av_id=112,
                bv_id="BVACTIVE02",
                title="Active Video 2",
                up_mid=9001,
                invalid=False,
                fav_time="2024-01-11 00:00:00",
            ),
        )
        upsert_video(
            conn,
            _build_video_payload(
                av_id=113,
                bv_id="BVINVALID1",
                title="已失效视频",
                up_mid=9002,
                invalid=True,
                fav_time="2024-01-12 00:00:00",
            ),
        )

        add_video_to_collection(conn, "BVACTIVE01", 501, "2024-01-10 00:00:00")
        add_video_to_collection(conn, "BVACTIVE02", 501, "2024-01-11 00:00:00")
        add_video_to_collection(conn, "BVINVALID1", 501, "2024-01-12 00:00:00")


def test_check_ytdlp_returns_version():
    service = DownloadService(
        subprocess_run=lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout="2026.01.01\n",
            stderr="",
        ),
    )

    result = service.check_ytdlp()

    assert result == {"success": True, "available": True, "version": "2026.01.01"}


def test_export_cookies_for_ytdlp_writes_netscape_file(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"cookie": "SESSDATA=aaa; DedeUserID=123"}),
        encoding="utf-8",
    )

    service = DownloadService()
    result = service.export_cookies_for_ytdlp(str(config_path))

    assert result["success"] is True
    cookie_file = result["cookie_file"]
    assert cookie_file

    text = open(cookie_file, "r", encoding="utf-8").read()
    assert "# Netscape HTTP Cookie File" in text
    assert ".bilibili.com\tTRUE\t/\tFALSE\t0\tSESSDATA\taaa" in text
    assert ".bilibili.com\tTRUE\t/\tFALSE\t0\tDedeUserID\t123" in text


def test_download_video_builds_expected_command(tmp_path):
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, "kwargs": kwargs})
        if cmd == ["yt-dlp", "--version"]:
            return SimpleNamespace(returncode=0, stdout="2026.01.01", stderr="")
        return SimpleNamespace(returncode=0)

    service = DownloadService(subprocess_run=fake_run)

    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text("dummy", encoding="utf-8")

    output_dir = tmp_path / "downloads"
    result = service.download_video(
        "BV1ABCDEF",
        str(output_dir),
        cookie_file=str(cookie_file),
        quality="1080p",
    )

    assert result["success"] is True
    assert output_dir.exists()

    assert len(calls) == 2
    assert calls[0]["cmd"] == ["yt-dlp", "--version"]

    cmd = calls[1]["cmd"]
    assert cmd[0] == "yt-dlp"
    assert "--cookies" in cmd
    assert str(cookie_file) in cmd
    assert "-f" in cmd
    assert "bestvideo[height<=1080]+bestaudio/best[height<=1080]" in cmd
    assert cmd[-1] == "https://www.bilibili.com/video/BV1ABCDEF"
    assert calls[1]["kwargs"]["timeout"] == 600


def test_download_collection_skips_invalid_and_existing(tmp_path, monkeypatch):
    db_path = get_db_path(str(tmp_path))
    init_db(db_path)
    _seed_download_fixture(db_path)

    output_base = tmp_path / "downloads"
    coll_dir = output_base / "Downloader Collection"
    coll_dir.mkdir(parents=True, exist_ok=True)
    (coll_dir / "already BVACTIVE01.mp4").write_text("exists", encoding="utf-8")

    service = DownloadService()
    monkeypatch.setattr(
        service,
        "check_ytdlp",
        lambda: {"success": True, "available": True, "version": "ok"},
    )

    download_calls = []

    def fake_download_video(bv_id, output_dir, cookie_file=None, quality="best", check_dependency=True):
        download_calls.append(
            {
                "bv_id": bv_id,
                "output_dir": output_dir,
                "cookie_file": cookie_file,
                "quality": quality,
                "check_dependency": check_dependency,
            }
        )
        return {"success": True, "bv_id": bv_id, "output_dir": output_dir}

    monkeypatch.setattr(service, "download_video", fake_download_video)

    result = service.download_collection(
        db_path=db_path,
        collection_id=501,
        output_base=str(output_base),
        quality="720p",
        cookie_file="cookie.txt",
    )

    assert result["success"] is True
    assert result["collection_name"] == "Downloader Collection"
    assert result["success_count"] == 1
    assert result["fail_count"] == 0
    assert result["skipped_invalid_count"] == 1
    assert result["skipped_existing_count"] == 1

    assert download_calls == [
        {
            "bv_id": "BVACTIVE02",
            "output_dir": str(coll_dir),
            "cookie_file": "cookie.txt",
            "quality": "720p",
            "check_dependency": False,
        }
    ]


def test_get_latest_collections_keeps_latest_by_name(tmp_path):
    db_path = get_db_path(str(tmp_path))
    init_db(db_path)

    with get_connection(db_path) as conn:
        conn.execute(
            "INSERT INTO collections (id, name, media_count, api_mtime, last_crawl_time) VALUES (?, ?, ?, ?, ?)",
            (10, "Same Name", 1, 1, "2024-01-01 00:00:00"),
        )
        conn.execute(
            "INSERT INTO collections (id, name, media_count, api_mtime, last_crawl_time) VALUES (?, ?, ?, ?, ?)",
            (11, "Same Name", 2, 2, "2024-02-01 00:00:00"),
        )
        conn.execute(
            "INSERT INTO collections (id, name, media_count, api_mtime, last_crawl_time) VALUES (?, ?, ?, ?, ?)",
            (12, "Other", 1, 1, "2024-03-01 00:00:00"),
        )
        conn.execute(
            "INSERT INTO ups (mid, name, face_url) VALUES (?, ?, ?)",
            (77, "up", "https://example.invalid/up.jpg"),
        )
        conn.execute(
            "INSERT INTO videos (bv_id, title, up_mid, is_invalid) VALUES (?, ?, ?, ?)",
            ("BVX", "title", 77, 0),
        )
        conn.execute(
            "INSERT INTO video_collection (bv_id, collection_id, fav_time, is_active) VALUES (?, ?, ?, 1)",
            ("BVX", 11, "2024-02-01 00:00:00"),
        )

    service = DownloadService()
    rows = service.get_latest_collections(db_path)

    assert [row["name"] for row in rows] == ["Other", "Same Name"]
    same_name = next(row for row in rows if row["name"] == "Same Name")
    assert same_name["id"] == 11
    assert same_name["active_count"] == 1
