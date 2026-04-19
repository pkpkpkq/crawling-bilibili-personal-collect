from pathlib import Path


def test_no_legacy_export_references_anywhere_in_repo():
    root = Path(__file__).resolve().parents[1]
    skip_dirs = {'.git', '.venv', 'venv', '__pycache__', '.sisyphus'}
    skip_prefixes = {'test_no_legacy_export', 'test_no_' + 'c' + 'sv'}
    removed_flag = 'c' + 'sv_export'
    removed_func = 'export_all_videos_' + 'c' + 'sv'

    for path in root.rglob('*'):
        if any(part in skip_dirs for part in path.parts):
            continue
        if path.is_dir() or any(path.name.startswith(prefix) for prefix in skip_prefixes):
            continue
        if path.suffix.lower() not in {'.py', '.js', '.md', '.json', '.html', '.txt'}:
            continue

        text = path.read_text(encoding='utf-8', errors='ignore')
        assert removed_flag not in text, path
        assert removed_func not in text, path
