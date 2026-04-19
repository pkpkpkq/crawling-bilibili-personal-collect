from app.workers.download_worker import DownloadWorker


class StubDownloadService:
    def __init__(self):
        self.cookie_result = {"success": True, "cookie_file": "cookies.txt"}
        self.video_result = {
            "success": True,
            "bv_id": "BV123456",
            "output_dir": "downloads",
            "error": None,
        }
        self.collection_result = {
            "success": True,
            "collection_id": 7,
            "collection_name": "Fav A",
            "output_dir": "downloads/Fav A",
            "success_count": 3,
            "fail_count": 0,
            "skipped_invalid_count": 1,
            "skipped_existing_count": 2,
            "error": None,
        }

        self.cookie_calls = []
        self.video_calls = []
        self.collection_calls = []

    def export_cookies_for_ytdlp(self, config_path="config.json"):
        self.cookie_calls.append(config_path)
        return dict(self.cookie_result)

    def download_video(self, bv_id, output_dir, cookie_file=None, quality="best"):
        self.video_calls.append(
            {
                "bv_id": bv_id,
                "output_dir": output_dir,
                "cookie_file": cookie_file,
                "quality": quality,
            }
        )
        result = dict(self.video_result)
        result.setdefault("bv_id", bv_id)
        result.setdefault("output_dir", output_dir)
        return result

    def download_collection(
        self,
        db_path,
        collection_id,
        output_base="downloads",
        quality="best",
        cookie_file=None,
    ):
        self.collection_calls.append(
            {
                "db_path": db_path,
                "collection_id": collection_id,
                "output_base": output_base,
                "quality": quality,
                "cookie_file": cookie_file,
            }
        )
        result = dict(self.collection_result)
        result.setdefault("collection_id", collection_id)
        return result


def test_download_worker_single_mode_success_emits_summary(qtbot):
    service = StubDownloadService()
    worker = DownloadWorker(
        mode="single",
        bv_id="123456",
        quality="720p",
        output_base="downloads",
        config_path="custom-config.json",
        download_service=service,
    )

    status_messages = []
    worker.status_changed.connect(status_messages.append)

    with qtbot.waitSignal(worker.download_succeeded, timeout=2000) as blocker:
        worker.start()

    worker.wait(1000)

    summary = blocker.args[0]
    assert summary["success"] is True
    assert summary["mode"] == "single"
    assert summary["bv_id"] == "BV123456"
    assert summary["success_count"] == 1
    assert summary["fail_count"] == 0
    assert summary["cookie_warning"] is None

    assert service.cookie_calls == ["custom-config.json"]
    assert service.video_calls == [
        {
            "bv_id": "BV123456",
            "output_dir": "downloads",
            "cookie_file": "cookies.txt",
            "quality": "720p",
        }
    ]
    assert service.collection_calls == []
    assert any("正在下载视频" in message for message in status_messages)


def test_download_worker_collection_mode_success_emits_summary(qtbot):
    service = StubDownloadService()
    worker = DownloadWorker(
        mode="collection",
        collection_id=7,
        quality="480p",
        output_base="my-downloads",
        db_path="fixture.db",
        download_service=service,
    )

    progress_events = []
    worker.progress_changed.connect(lambda current, total: progress_events.append((current, total)))

    with qtbot.waitSignal(worker.download_succeeded, timeout=2000) as blocker:
        worker.start()

    worker.wait(1000)

    summary = blocker.args[0]
    assert summary["success"] is True
    assert summary["mode"] == "collection"
    assert summary["collection_id"] == 7
    assert summary["collection_name"] == "Fav A"
    assert summary["success_count"] == 3
    assert summary["fail_count"] == 0
    assert summary["skipped_invalid_count"] == 1
    assert summary["skipped_existing_count"] == 2

    assert service.collection_calls == [
        {
            "db_path": "fixture.db",
            "collection_id": 7,
            "output_base": "my-downloads",
            "quality": "480p",
            "cookie_file": "cookies.txt",
        }
    ]
    assert progress_events[0] == (0, 0)
    assert progress_events[-1] == (1, 1)


def test_download_worker_missing_cookie_is_warning_and_continues(qtbot):
    service = StubDownloadService()
    service.cookie_result = {
        "success": False,
        "cookie_file": None,
        "error": {"code": "cookie_missing", "message": "config.json 中没有 cookie"},
    }

    worker = DownloadWorker(
        mode="single",
        bv_id="BV1abc",
        quality="best",
        output_base="downloads",
        download_service=service,
    )

    with qtbot.waitSignal(worker.download_succeeded, timeout=2000) as blocker:
        worker.start()

    worker.wait(1000)

    summary = blocker.args[0]
    assert summary["success"] is True
    assert summary["cookie_warning"] == {
        "code": "cookie_missing",
        "message": "config.json 中没有 cookie",
    }
    assert service.video_calls[0]["cookie_file"] is None


def test_download_worker_reports_missing_ytdlp_failure(qtbot):
    service = StubDownloadService()
    service.video_result = {
        "success": False,
        "error": {
            "code": "missing_ytdlp",
            "message": "未找到 yt-dlp，请先安装: pip install yt-dlp",
            "details": {"install_url": "https://github.com/yt-dlp/yt-dlp"},
        },
    }

    worker = DownloadWorker(
        mode="single",
        bv_id="BV777",
        quality="1080p",
        output_base="downloads",
        download_service=service,
    )

    with qtbot.waitSignal(worker.download_failed, timeout=2000) as blocker:
        worker.start()

    worker.wait(1000)

    summary = blocker.args[0]
    assert summary["success"] is False
    assert summary["mode"] == "single"
    assert summary["fail_count"] == 1
    assert summary["error"]["code"] == "missing_ytdlp"


def test_download_worker_cookie_export_fatal_error_fails_job(qtbot):
    service = StubDownloadService()
    service.cookie_result = {
        "success": False,
        "cookie_file": None,
        "error": {
            "code": "unexpected_cookie_error",
            "message": "cookie exporter exploded",
        },
    }

    worker = DownloadWorker(
        mode="collection",
        collection_id=1,
        quality="best",
        output_base="downloads",
        download_service=service,
    )

    with qtbot.waitSignal(worker.download_failed, timeout=2000) as blocker:
        worker.start()

    worker.wait(1000)

    summary = blocker.args[0]
    assert summary["success"] is False
    assert summary["mode"] == "collection"
    assert summary["error"]["code"] == "unexpected_cookie_error"
    assert service.collection_calls == []


def test_download_worker_invalid_mode_fails(qtbot):
    service = StubDownloadService()
    worker = DownloadWorker(
        mode="unknown",
        download_service=service,
    )

    with qtbot.waitSignal(worker.download_failed, timeout=2000) as blocker:
        worker.start()

    worker.wait(1000)

    summary = blocker.args[0]
    assert summary["success"] is False
    assert summary["error"]["code"] == "invalid_mode"


def test_download_worker_without_cookie_skips_cookie_export(qtbot):
    service = StubDownloadService()
    worker = DownloadWorker(
        mode="single",
        bv_id="BV2222",
        use_cookie=False,
        download_service=service,
    )

    with qtbot.waitSignal(worker.download_succeeded, timeout=2000):
        worker.start()

    worker.wait(1000)

    assert service.cookie_calls == []
    assert service.video_calls[0]["cookie_file"] is None
