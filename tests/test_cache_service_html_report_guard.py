from pathlib import Path


def test_no_html_report_asset_canonical_references_in_runtime_code():
    root = Path(__file__).resolve().parents[1]
    target_files = [
        root / "app" / "services" / "crawl_service.py",
        root / "app" / "repositories" / "core.py",
        root / "viewing.py",
        root / "templates" / "main.js",
    ]

    forbidden = [
        "视频封面/",
        "up头像/",
        "'html_report/' + video.info.cover_path",
        '"html_report/" + video.info.cover_path',
        "'html_report/' + video.info.up_face_path",
        '"html_report/" + video.info.up_face_path',
    ]

    for path in target_files:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in text, f"{path} still contains forbidden asset token: {token}"


def test_cache_service_defines_expected_cache_layout():
    root = Path(__file__).resolve().parents[1]
    cache_service_py = root / "app" / "services" / "cache_service.py"
    text = cache_service_py.read_text(encoding="utf-8")

    assert 'CACHE_ROOT = "cache"' in text
    assert 'COVERS_DIR = "covers"' in text
    assert 'UP_FACES_DIR = "up_faces"' in text
