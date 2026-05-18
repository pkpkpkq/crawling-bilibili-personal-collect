import pytest
from pathlib import Path
from PySide6.QtWidgets import QLabel
from PySide6.QtCharts import QChartView
from PySide6.QtGui import QColor
from app.ui.pages.dashboard_page import DashboardPage
from app.ui.components.page_header import PageHeader
from app.ui.components.summary_card import SummaryCard
from app.ui import strings
from app.theme import CHART_PALETTE


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

    # PageHeader with Chinese title
    headers = page.findChildren(PageHeader)
    assert len(headers) >= 1
    assert headers[0].title_label.text() == strings.PAGE_TITLE_DATA_OVERVIEW

    # SummaryCard values
    cards = page.findChildren(SummaryCard)
    assert len(cards) == 5
    card_titles = [c.title_label.text() for c in cards]
    assert strings.SUMMARY_TOTAL_VIDEOS in card_titles
    assert strings.SUMMARY_TOTAL_COLLECTIONS in card_titles
    assert strings.SUMMARY_TOTAL_UPS in card_titles
    assert strings.SUMMARY_FOLLOWING_UPS in card_titles
    assert strings.SUMMARY_INVALID_VIDEOS in card_titles
    card_values = [c.value_label.text() for c in cards]
    assert "100" in card_values
    assert "5" in card_values

    # Charts
    chart_views = page.findChildren(QChartView)
    assert len(chart_views) == 3

    # Insight card section titles (SurfaceCard with QLabel#h2 children)
    labels = page.findChildren(QLabel)
    all_text = [label.text() for label in labels]
    assert strings.LIST_TOP_UPS in all_text
    assert strings.LIST_RECENT_INVALID in all_text
    assert strings.LIST_RECENT_UNFAV in all_text


def test_dashboard_chart_palette_applied(qapp, mock_stats):
    page = DashboardPage(db_conn=MockConn())

    chart_views = page.findChildren(QChartView)

    pie_chart = chart_views[1].chart()
    pie_series = pie_chart.series()
    if pie_series:
        slices = pie_series[0].slices()
        for i, slice_ in enumerate(slices):
            expected = QColor(CHART_PALETTE[i % len(CHART_PALETTE)])
            actual = slice_.color()
            assert actual == expected, f"Pie slice {i} color mismatch"

    bar_chart = chart_views[0].chart()
    bar_series_list = bar_chart.series()
    if bar_series_list:
        bar_sets = bar_series_list[0].barSets()
        for i, bar_set in enumerate(bar_sets):
            expected = QColor(CHART_PALETTE[i % len(CHART_PALETTE)])
            actual = bar_set.color()
            assert actual == expected, f"Bar set {i} color mismatch"

    line_chart = chart_views[2].chart()
    line_series_list = line_chart.series()
    if line_series_list:
        pen = line_series_list[0].pen()
        assert pen.color() == QColor(CHART_PALETTE[0])


def test_dashboard_screenshot(qapp, mock_stats, tmp_path):
    page = DashboardPage(db_conn=MockConn())
    page.resize(1200, 800)
    path = str(tmp_path / "dashboard.png")
    page.grab().save(path)
    assert Path(path).exists()
    assert Path(path).stat().st_size > 0
