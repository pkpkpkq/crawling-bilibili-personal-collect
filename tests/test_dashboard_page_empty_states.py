import pytest
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.components.empty_state import EmptyState
from app.ui.components.summary_card import SummaryCard
from app.ui import strings


class MockConn:
    pass


@pytest.fixture
def mock_empty_stats(monkeypatch):
    data = {}
    monkeypatch.setattr("app.repositories.stats.get_stats", lambda conn: data)
    return data


def test_dashboard_empty_states(qapp, mock_empty_stats):
    page = DashboardPage(db_conn=MockConn())

    # SummaryCards render with default 0 values
    cards = page.findChildren(SummaryCard)
    assert len(cards) == 5
    card_titles = [c.title_label.text() for c in cards]
    assert strings.SUMMARY_TOTAL_VIDEOS in card_titles
    card_values = [c.value_label.text() for c in cards]
    assert "0" in card_values

    # EmptyState widgets appear in insight cards
    empty_states = page.findChildren(EmptyState)
    assert len(empty_states) >= 1

    # EmptyState shows Chinese empty text
    empty_titles = [es.title_label.text() for es in empty_states]
    assert strings.EMPTY_NO_DATA in empty_titles
