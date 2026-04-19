from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_legacy_html_report_artifacts_removed():
    forbidden_paths = [
        ROOT / 'server.py',
        ROOT / 'viewing.py',
        ROOT / 'getcookie.py',
        ROOT / 'downloader.py',
        ROOT / 'index.html',
        ROOT / 'templates',
        ROOT / 'html_report',
    ]

    for path in forbidden_paths:
        assert not path.exists(), f'legacy path still exists: {path}'


def test_cache_service_defines_expected_cache_layout():
    cache_service_py = ROOT / 'app' / 'services' / 'cache_service.py'
    text = cache_service_py.read_text(encoding='utf-8')

    assert 'CACHE_ROOT = "cache"' in text
    assert 'COVERS_DIR = "covers"' in text
    assert 'UP_FACES_DIR = "up_faces"' in text
