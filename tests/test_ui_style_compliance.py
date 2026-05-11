"""UI style compliance tests — enforce design-system discipline in page files.

These tests read source files as TEXT (no import) to catch violations
without needing a running QApplication.
"""

import re
import glob
import os

from app.theme import CHART_PALETTE, Color


PAGES_DIR = os.path.join("app", "ui", "pages")
COMPONENTS_DIR = os.path.join("app", "ui", "components")
PAGE_FILES = glob.glob(os.path.join(PAGES_DIR, "*.py"))
COMPONENT_FILES = glob.glob(os.path.join(COMPONENTS_DIR, "*.py"))
MAIN_WINDOW_FILE = os.path.join("app", "ui", "main_window.py")
ALL_UI_FILES = PAGE_FILES + COMPONENT_FILES + [MAIN_WINDOW_FILE]

_BOLD_VIOLATIONS = {
    os.path.join(PAGES_DIR, "collection_page.py"),
    os.path.join(PAGES_DIR, "dashboard_page.py"),
    os.path.join(PAGES_DIR, "up_list_page.py"),
}
_FOCUS_BLUE_VIOLATIONS: set[str] = set()

_HEX_RE = re.compile(r"(?<!\w)#[0-9a-fA-F]{6}\b")


def _read_file(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _strip_comments(source: str) -> str:
    lines = []
    for line in source.splitlines():
        stripped = line.lstrip()
        if not stripped.startswith("#"):
            lines.append(line)
    return "\n".join(lines)


def test_no_raw_hex_colors_in_pages():
    for path in ALL_UI_FILES:
        source = _read_file(path)
        clean = _strip_comments(source)
        matches = _HEX_RE.findall(clean)
        assert matches == [], (
            f"{path} contains raw hex colors {matches}; "
            "use app.theme.Color tokens instead"
        )


def test_no_font_weight_bold_in_pages():
    for path in ALL_UI_FILES:
        source = _read_file(path)
        clean = _strip_comments(source)
        if os.path.normpath(path) in {os.path.normpath(p) for p in _BOLD_VIOLATIONS}:
            continue
        assert "font-weight: bold" not in clean, (
            f"{path} uses 'font-weight: bold'; "
            "use FontWeight.MEDIUM (500) via theme tokens instead"
        )
        assert "font.setBold(True)" not in clean, (
            f"{path} uses font.setBold(True); "
            "use QFont.Weight.Medium or FontWeight.MEDIUM instead"
        )


def test_no_focus_blue_link_usage_in_pages():
    for path in ALL_UI_FILES:
        source = _read_file(path)
        if os.path.normpath(path) in {os.path.normpath(p) for p in _FOCUS_BLUE_VIOLATIONS}:
            continue
        assert "Color.FOCUS_BLUE" not in source, (
            f"{path} references Color.FOCUS_BLUE; "
            "FOCUS_BLUE is reserved for QLineEdit/QTextEdit/QSpinBox "
            "focus rings in theme.py base stylesheet only. "
            "Use LINK_COLOR_DEFAULT / LINK_COLOR_HOVER for links."
        )


def test_chart_palette_warm_only():
    all_color_values = [v.value for v in Color]
    for entry in CHART_PALETTE:
        assert entry in all_color_values, (
            f"CHART_PALETTE entry '{entry}' is not a valid Color enum value"
        )


_SETINDEX_WIDGET_FORBIDDEN = {
    os.path.join(PAGES_DIR, "collection_page.py"),
    os.path.join(PAGES_DIR, "search_page.py"),
}


def test_no_set_index_widget_in_card_pages():
    for path in _SETINDEX_WIDGET_FORBIDDEN:
        source = _read_file(path)
        assert "setIndexWidget" not in source, (
            f"{path} uses setIndexWidget; "
            "use delegate-based painting with toggleExpanded / hitTestLink instead"
        )
        assert "setItemWidget" not in source, (
            f"{path} uses setItemWidget; "
            "use QStyledItemDelegate for custom item painting instead"
        )
