from pathlib import Path


def test_no_csv_references_anywhere_in_repo():
    root = Path(__file__).resolve().parents[1]
    skip_dirs = {".git", ".venv", "venv", "__pycache__", ".sisyphus"}
    for path in root.rglob("*"):
        if any(part in skip_dirs for part in path.parts):
            continue
        if path.is_dir() or path.name.startswith("test_no_csv"):
            continue
        if path.suffix.lower() not in {".py", ".js", ".md", ".json", ".html", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        assert "csv_export" not in text, path
        assert "export_all_videos_csv" not in text, path
