from pathlib import Path


def test_no_legacy_export_symbols_remain():
    root = Path(__file__).resolve().parents[1]
    targets = [
        root / 'main.py',
        root / 'app/repositories/core.py',
        root / 'app/repositories/videos.py',
        root / 'app/repositories/__init__.py',
        root / 'database.py',
        root / 'app/services/config_service.py',
        root / 'README.md',
    ]

    removed_flag = 'c' + 'sv_export'
    removed_func = 'export_all_videos_' + 'c' + 'sv'
    removed_label = 'C' + 'SV 导出'

    for path in targets:
        text = path.read_text(encoding='utf-8')
        assert removed_flag not in text, path
        assert removed_func not in text, path
        assert removed_label not in text, path


def test_legacy_html_files_are_removed():
    root = Path(__file__).resolve().parents[1]
    for path in [
        root / 'viewing.py',
        root / 'server.py',
        root / 'getcookie.py',
        root / 'downloader.py',
        root / 'index.html',
        root / 'templates',
        root / 'html_report',
    ]:
        assert not path.exists(), path
