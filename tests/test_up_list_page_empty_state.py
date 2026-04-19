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


def test_empty_state_initialization(qtbot):
    page = UpListPage()
    qtbot.addWidget(page)

    assert page.source_model.rowCount() == 0
    assert page.filter_proxy.rowCount() == 0


def test_empty_state_with_no_data(qtbot, mock_db_connection, mock_following_repo):
    page = UpListPage()
    qtbot.addWidget(page)

    mock_following_repo.return_value = []
    page.load_data()

    assert page.source_model.rowCount() == 0
    assert page.filter_proxy.rowCount() == 0

    page.search_input.setText("any text")
    assert page.filter_proxy.rowCount() == 0
