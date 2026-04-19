from app.services.download_service import DownloadService


def test_check_ytdlp_returns_structured_missing_dependency_error():
    service = DownloadService(subprocess_run=lambda *args, **kwargs: (_ for _ in ()).throw(FileNotFoundError()))

    result = service.check_ytdlp()

    assert result["success"] is False
    assert result["available"] is False
    assert result["error"]["code"] == "missing_ytdlp"
    assert "pip install yt-dlp" in result["error"]["message"]


def test_download_video_returns_structured_missing_dependency_error(monkeypatch, tmp_path):
    service = DownloadService()
    monkeypatch.setattr(
        service,
        "check_ytdlp",
        lambda: {
            "success": False,
            "available": False,
            "error": {
                "code": "missing_ytdlp",
                "message": "未找到 yt-dlp，请先安装: pip install yt-dlp",
            },
        },
    )

    result = service.download_video("BVNOYT01", str(tmp_path / "downloads"))

    assert result["success"] is False
    assert result["error"]["code"] == "missing_ytdlp"
    assert result["bv_id"] == "BVNOYT01"


def test_download_collection_returns_structured_missing_dependency_error(monkeypatch, tmp_path):
    service = DownloadService()
    monkeypatch.setattr(
        service,
        "check_ytdlp",
        lambda: {
            "success": False,
            "available": False,
            "error": {
                "code": "missing_ytdlp",
                "message": "未找到 yt-dlp，请先安装: pip install yt-dlp",
            },
        },
    )

    result = service.download_collection(
        db_path=str(tmp_path / "db.sqlite"),
        collection_id=1,
    )

    assert result["success"] is False
    assert result["error"]["code"] == "missing_ytdlp"
    assert result["collection_id"] == 1
    assert result["success_count"] == 0
    assert result["fail_count"] == 0
