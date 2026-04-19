import pytest
from PySide6.QtWidgets import QLabel
from PySide6.QtCharts import QChartView
from app.ui.pages.dashboard_page import DashboardPage


class MockConn:
    pass


@pytest.fixture
def mock_stats(monkeypatch):
    data = {
        "total_videos": 100,
        "total_collections": 5,
        "total_ups": 20,
        "following_ups": 10,
        "invalid_videos": 2,
        "collection_counts": [{"name": "Col 1", "count": 50}],
        "top_ups": [{"name": "UP 1", "mid": 1, "count": 10}],
        "monthly_trend": [{"month": "2023-10", "count": 5}],
        "recent_invalid": [
            {"title": "Inv 1", "bv_id": "BV1", "up_name": "UP 1", "collection": "Col 1"}
        ],
        "recent_unfav": [
            {
                "title": "Unf 1",
                "bv_id": "BV2",
                "up_name": "UP 2",
                "collection": "Col 1",
                "unfav_time": "2023",
            }
        ],
        "duration_distribution": {"<1分钟": 10, "1-5分钟": 90},
        "crawl_history": [],
    }
    monkeypatch.setattr("app.repositories.stats.get_stats", lambda conn: data)
    return data


def test_dashboard_page_renders_sections(qapp, mock_stats):
    page = DashboardPage(db_conn=MockConn())

    # Check for title
    labels = page.findChildren(QLabel)
    titles = [label.text() for label in labels]
    assert "Dashboard" in titles

    # Check for summary values
    assert "100" in titles  # Total videos
    assert "5" in titles  # Total collections

    # Check for charts presence
    chart_views = page.findChildren(QChartView)
    assert len(chart_views) == 3  # Collection, Duration, Trend

    # Check for lists
    assert "Top UPs" in titles
    assert "Recent Invalid" in titles
    assert "Recent Unfavorited" in titles
