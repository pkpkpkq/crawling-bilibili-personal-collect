import downloader


class StubDownloadService:
    def __init__(self):
        self.check_result = {"success": True}
        self.cookie_result = {"success": True, "cookie_file": "cookie.txt"}
        self.collections = [{"id": 1, "name": "Fav A", "active_count": 2}]
        self.download_video_calls = []
        self.download_collection_calls = []

    def check_ytdlp(self):
        return self.check_result

    def download_video(self, bv_id, output_dir, cookie_file=None, quality="best"):
        self.download_video_calls.append(
            {
                "bv_id": bv_id,
                "output_dir": output_dir,
                "cookie_file": cookie_file,
                "quality": quality,
            }
        )
        return {"success": True}

    def export_cookies_for_ytdlp(self, config_path="config.json"):
        return self.cookie_result

    def get_latest_collections(self, db_path):
        return self.collections

    def download_collection(
        self,
        db_path,
        collection_id,
        output_base="downloads",
        quality="best",
        cookie_file=None,
    ):
        self.download_collection_calls.append(
            {
                "db_path": db_path,
                "collection_id": collection_id,
                "output_base": output_base,
                "quality": quality,
                "cookie_file": cookie_file,
            }
        )
        return {
            "success": True,
            "success_count": 3,
            "fail_count": 1,
        }


def test_wrapper_functions_delegate_to_download_service():
    service = StubDownloadService()

    assert downloader.check_ytdlp(service=service) is True
    assert (
        downloader.download_video(
            "BV1XX", "downloads", cookie_file="cookies.txt", quality="720p", service=service
        )
        is True
    )
    assert downloader.export_cookies_for_ytdlp(service=service) == "cookie.txt"
    assert downloader.get_latest_collections("db.sqlite", service=service) == service.collections
    assert downloader.download_collection(
        "db.sqlite",
        1,
        output_base="downloads",
        quality="480p",
        cookie_file="cookies.txt",
        service=service,
    ) == (3, 1)


def test_interactive_download_shows_missing_ytdlp_message(monkeypatch, capsys):
    service = StubDownloadService()
    service.check_result = {"success": False, "error": {"code": "missing_ytdlp"}}

    monkeypatch.setattr(downloader, "_get_service", lambda: service)

    downloader.interactive_download("db.sqlite")

    out = capsys.readouterr().out
    assert "未找到 yt-dlp" in out
    assert not service.download_video_calls
    assert not service.download_collection_calls


def test_interactive_download_single_video_flow_delegates(monkeypatch):
    service = StubDownloadService()

    inputs = iter(["a", "123", "720p", "q"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr(downloader, "_get_service", lambda: service)

    downloader.interactive_download("fixture.db")

    assert service.download_video_calls == [
        {
            "bv_id": "BV123",
            "output_dir": "downloads",
            "cookie_file": "cookie.txt",
            "quality": "720p",
        }
    ]
    assert service.download_collection_calls == []


def test_interactive_download_collection_flow_delegates(monkeypatch):
    service = StubDownloadService()

    inputs = iter(["1", "480p", "q"])
    monkeypatch.setattr("builtins.input", lambda prompt="": next(inputs))
    monkeypatch.setattr(downloader, "_get_service", lambda: service)

    downloader.interactive_download("fixture.db")

    assert service.download_video_calls == []
    assert service.download_collection_calls == [
        {
            "db_path": "fixture.db",
            "collection_id": 1,
            "output_base": "downloads",
            "quality": "480p",
            "cookie_file": "cookie.txt",
        }
    ]
