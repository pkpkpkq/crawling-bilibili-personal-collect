import os

from app.repositories.connection import get_connection, init_db
from app.repositories.videos import get_all_videos_index, upsert_video
from app.services.cache_service import CacheService
from app.services.crawl_service import CrawlService


def _build_video_payload(*, bv_id: str = "BV_CACHE_001", up_mid: int = 114514):
    return {
        "id": 42,
        "BV": bv_id,
        "是否失效": False,
        "up主": {"ID": up_mid, "昵称": "CacheUP", "头像": "https://example.invalid/up.jpg"},
        "视频信息": {
            "标题": "Cache Video",
            "封面": f"https://example.invalid/{bv_id}.jpg",
            "简介": "cache",
            "时长": "00:01:00",
        },
        "观众数据": {"播放量": 1, "收藏量": 2, "弹幕数量": 3},
        "三个时间": {
            "上传时间": "2024-01-01 00:00:00",
            "发布时间": "2024-01-01 00:00:00",
            "收藏时间": "2024-01-02 00:00:00",
        },
    }


def test_cache_service_resolves_relative_and_report_paths():
    service = CacheService()

    assert service.get_cover_relative_path("BV1") == "cache/covers/BV1.jpg"
    assert service.get_up_face_relative_path(100) == "cache/up_faces/100.jpg"
    assert service.get_cover_report_path("BV1") == "../cache/covers/BV1.jpg"
    assert service.get_up_face_report_path(100) == "../cache/up_faces/100.jpg"


def test_cache_service_creates_cache_directories_lazily(tmp_path):
    base_dir = str(tmp_path)
    service = CacheService(base_dir=base_dir)

    cover_dir = tmp_path / "cache" / "covers"
    face_dir = tmp_path / "cache" / "up_faces"
    assert not cover_dir.exists()
    assert not face_dir.exists()

    cover_path = service.get_cover_file_path("BV_LAZY")
    assert cover_dir.is_dir()
    assert cover_path == str(cover_dir / "BV_LAZY.jpg")

    face_path = service.get_up_face_file_path("9527")
    assert face_dir.is_dir()
    assert face_path == str(face_dir / "9527.jpg")


def test_repository_video_index_uses_cache_service_paths(tmp_path):
    db_path = str(tmp_path / "bilibili_data.db")
    init_db(db_path)

    with get_connection(db_path) as conn:
        upsert_video(conn, _build_video_payload())
        index = get_all_videos_index(conn, cache_service=CacheService())

    info = index["BV_CACHE_001"]["info"]
    assert info["cover_path"] == "cache/covers/BV_CACHE_001.jpg"
    assert info["up_face_path"] == "cache/up_faces/114514.jpg"


def test_crawl_sync_images_downloads_into_cache_directories(tmp_path, monkeypatch):
    db_path = str(tmp_path / "bilibili_data.db")
    init_db(db_path)

    with get_connection(db_path) as conn:
        upsert_video(conn, _build_video_payload(bv_id="BV_IMG_001", up_mid=7788))

    captured_paths = []

    def fake_fetch_image(url, path, retry_count=3):
        captured_paths.append((url, path, retry_count))
        return True

    service = CrawlService(sleep_func=lambda _: None)
    monkeypatch.setattr(service, "fetch_image", fake_fetch_image)

    result = service.sync_images(
        db_path,
        settings={"max_workers_image": 2, "image_retry": 1},
        cache_service=CacheService(base_dir=str(tmp_path)),
    )

    assert result["total"] == 2
    assert result["success"] == 2

    targets = [item[1] for item in captured_paths]
    assert os.path.join("cache", "covers", "BV_IMG_001.jpg") in targets[0] or os.path.join("cache", "covers", "BV_IMG_001.jpg") in targets[1]
    assert os.path.join("cache", "up_faces", "7788.jpg") in targets[0] or os.path.join("cache", "up_faces", "7788.jpg") in targets[1]
