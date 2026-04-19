import pytest
from PySide6.QtWidgets import QLabel
from app.ui.pages.dashboard_page import DashboardPage


class MockConn:
    pass


@pytest.fixture
def mock_empty_stats(monkeypatch):
    data = {}
    monkeypatch.setattr("app.repositories.stats.get_stats", lambda conn: data)
    return data


def test_dashboard_empty_states(qapp, mock_empty_stats):
    page = DashboardPage(db_conn=MockConn())

    # Empty layout shouldn't throw error and should display empty states
    # e.g., 'No data available' text.
    labels = [l.text() for l in page.findChildren(QLabel)]

    assert "Total Videos" in labels
    assert "0" in labels

    assert "No data available" in labels
