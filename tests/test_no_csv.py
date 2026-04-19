from pathlib import Path

def test_no_csv_export_symbols_remain():
    root = Path(__file__).resolve().parents[1]
    targets = [root / "main.py", root / "app/repositories/core.py", root / "app/repositories/videos.py", root / "app/repositories/__init__.py", root / "database.py", root / "app/services/config_service.py", root / "viewing.py", root / "templates/main.js", root / "README.md"]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        assert "csv_export" not in text, path
        assert "export_all_videos_csv" not in text, path
        assert "CSV 导出" not in text, path
