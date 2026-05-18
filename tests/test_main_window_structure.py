from pathlib import Path

from PySide6.QtCore import Qt
from app.ui.main_window import MainWindow
from app.ui import strings


def test_main_window_creation(qapp):
    window = MainWindow()
    assert window is not None
    assert window.windowTitle() == strings.WINDOW_TITLE

    assert window.centralWidget() is not None
    layout = window.centralWidget().layout()
    assert layout is not None

    widgets = [layout.itemAt(i).widget() for i in range(layout.count())]
    # Nav list is now inside a nav-panel QWidget container
    assert any(w.objectName() == "nav-panel" for w in widgets if w is not None)
    assert any(w.metaObject().className() == "QStackedWidget" for w in widgets)


def test_nav_list_object_name_and_count(qapp):
    window = MainWindow()
    assert window.nav_list.objectName() == "nav-list"
    assert window.nav_list.count() == 7


def test_page_stack_object_name_and_count(qapp):
    window = MainWindow()
    assert window.pages_stack.objectName() == "page-stack"
    assert window.pages_stack.count() == 7


def test_page_object_names(qapp):
    window = MainWindow()
    expected_names = [
        ("dashboard_page", "page-dashboard"),
        ("collection_page", "page-collection"),
        ("search_page", "page-search"),
        ("up_list_page", "page-ups"),
        ("settings_page", "page-settings"),
        ("crawl_page", "page-crawl"),
        ("downloads_page", "page-downloads"),
    ]
    for attr_name, obj_name in expected_names:
        page = getattr(window, attr_name)
        assert page.objectName() == obj_name, (
            f"{attr_name}.objectName() expected {obj_name!r}, got {page.objectName()!r}"
        )


def test_nav_items_use_strings_constants(qapp):
    window = MainWindow()
    expected_labels = [
        strings.NAV_DATA_OVERVIEW,
        strings.NAV_COLLECTION,
        strings.NAV_GLOBAL_SEARCH,
        strings.NAV_FOLLOWING_UP,
        strings.NAV_SETTINGS,
        strings.NAV_CRAWL,
        strings.NAV_DOWNLOADS,
    ]
    for i, expected in enumerate(expected_labels):
        item = window.nav_list.item(i)
        assert item.text() == expected, (
            f"nav_list item {i}: text expected {expected!r}, got {item.text()!r}"
        )


def test_main_window_collection_list_and_selection(qapp, seeded_fixture_db, monkeypatch):
    monkeypatch.setattr("app.ui.main_window.get_db_path", lambda: str(seeded_fixture_db))

    window = MainWindow()

    window.nav_list.setCurrentRow(1)
    assert window.collection_page.page_stack.currentWidget() == window.collection_page.list_page
    assert window.collection_page.title_label.text() == "收藏夹"
    assert window.collection_page.collection_list.count() > 0

    item = window.collection_page.collection_list.item(0)
    window.collection_page.collection_selected.emit(item.data(Qt.ItemDataRole.UserRole), item.text())

    assert window.collection_page.page_stack.currentWidget() == window.collection_page.detail_page
    window.collection_page.back_btn.click()
    assert window.collection_page.page_stack.currentWidget() == window.collection_page.list_page


def test_main_window_returns_collection_to_list_on_reentry(qapp, seeded_fixture_db, monkeypatch):
    monkeypatch.setattr("app.ui.main_window.get_db_path", lambda: str(seeded_fixture_db))

    window = MainWindow()
    window.nav_list.setCurrentRow(1)
    item = window.collection_page.collection_list.item(0)
    window.collection_page.collection_selected.emit(item.data(Qt.ItemDataRole.UserRole), item.text())

    window.nav_list.setCurrentRow(0)
    window.nav_list.setCurrentRow(1)

    assert window.collection_page.page_stack.currentWidget() == window.collection_page.list_page


def test_screenshot_main_window_offscreen(qapp, tmp_path):
    """Grab the MainWindow at 800x540 offscreen for visual evidence."""
    window = MainWindow()
    window.resize(800, 540)
    screenshot_path = tmp_path / "main_window_800x540.png"
    window.grab().save(str(screenshot_path))
    assert screenshot_path.exists()
    assert screenshot_path.stat().st_size > 0
