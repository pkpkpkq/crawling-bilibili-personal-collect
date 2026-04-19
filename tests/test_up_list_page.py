import pytest
from PySide6.QtWidgets import QListView

from app.models import UpListRowRole
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


def test_up_list_page_initialization(qtbot):
    page = UpListPage()
    qtbot.addWidget(page)

    assert page.search_input.placeholderText() == "Filter by UP name..."
    assert isinstance(page.list_view, QListView)
    assert page.source_model.rowCount() == 0


def test_up_list_page_loads_data(qtbot, mock_db_connection, mock_following_repo):
    page = UpListPage()
    qtbot.addWidget(page)

    mock_following_repo.return_value = [
        {"mid": 123, "name": "Test UP", "face_url": "http://example.com/face.jpg"},
        {"mid": 456, "name": "Another UP", "face_url": "http://example.com/face2.jpg"},
    ]

    page.load_data()

    assert page.source_model.rowCount() == 2
    assert page.filter_proxy.rowCount() == 2


def test_up_list_page_filtering(qtbot, mock_db_connection, mock_following_repo):
    page = UpListPage()
    qtbot.addWidget(page)

    mock_following_repo.return_value = [
        {"mid": 123, "name": "Alpha", "face_url": ""},
        {"mid": 456, "name": "Bravo", "face_url": ""},
        {"mid": 789, "name": "Charlie", "face_url": ""},
    ]

    page.load_data()
    assert page.filter_proxy.rowCount() == 3

    page.search_input.setText("lph")
    assert page.filter_proxy.rowCount() == 1
    index = page.filter_proxy.index(0, 0)
    assert page.filter_proxy.data(index, int(UpListRowRole.NAME)) == "Alpha"

    page.search_input.setText("bra")
    assert page.filter_proxy.rowCount() == 1
    index = page.filter_proxy.index(0, 0)
    assert page.filter_proxy.data(index, int(UpListRowRole.NAME)) == "Bravo"

    page.search_input.setText("zzz")
    assert page.filter_proxy.rowCount() == 0
