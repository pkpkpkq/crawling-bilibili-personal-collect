import pytest

from app.ui.pages.up_list_page import UpListPage


@pytest.fixture
def mock_db_connection(mocker):
    conn_mock = mocker.MagicMock()
    mocker.patch(
        "app.ui.pages.up_list_page.get_connection",
        return_value=mocker.MagicMock(
            __enter__=lambda _: conn_mock, __exit__=lambda *args: None
        ),
    )
    return conn_mock


@pytest.fixture
def mock_following_repo(mocker):
    return mocker.patch("app.ui.pages.up_list_page.get_all_following_ups")


def test_click_emits_search_requested(qtbot, mock_db_connection, mock_following_repo):
    page = UpListPage()
    qtbot.addWidget(page)

    mock_following_repo.return_value = [
        {"mid": 123, "name": "Target UP", "face_url": ""},
    ]

    page.load_data()

    with qtbot.waitSignal(page.search_requested, timeout=1000) as blocker:
        index = page.filter_proxy.index(0, 0)
        page._on_list_clicked(index)

    assert blocker.args == ["Target UP"]


def test_click_webbrowser_open(qtbot, mocker, mock_db_connection, mock_following_repo):
    page = UpListPage()
    qtbot.addWidget(page)

    mock_following_repo.return_value = [
        {"mid": 999, "name": "BiliUP", "face_url": ""},
    ]

    page.load_data()

    mock_webbrowser = mocker.patch("app.ui.pages.up_list_page.webbrowser.open")

    from PySide6.QtCore import QEvent, QPoint, QRect, Qt
    from PySide6.QtGui import QMouseEvent

    index = page.filter_proxy.index(0, 0)
    page.delegate.link_rects[index] = QRect(10, 10, 100, 20)

    event = QMouseEvent(
        QEvent.Type.MouseButtonRelease,
        QPoint(50, 15),
        Qt.MouseButton.LeftButton,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
    )

    handled = page.delegate.editorEvent(event, page.filter_proxy, None, index)

    assert handled is True
    mock_webbrowser.assert_called_once_with("https://space.bilibili.com/999")
