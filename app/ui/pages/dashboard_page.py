from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGridLayout,
    QScrollArea,
    QFrame,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QMargins
from PySide6.QtGui import QPainter
from PySide6.QtCharts import (
    QChart,
    QChartView,
    QPieSeries,
    QBarSeries,
    QBarSet,
    QBarCategoryAxis,
    QValueAxis,
    QLineSeries,
)
from app.theme import Color, Typography, Spacing, BorderRadius
from app.repositories import stats


class DashboardPage(QWidget):
    def __init__(self, db_conn, parent=None):
        super().__init__(parent)
        self.db_conn = db_conn
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background-color: transparent; }")

        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(
            Spacing.SCALE_32, Spacing.SCALE_32, Spacing.SCALE_32, Spacing.SCALE_32
        )
        self.content_layout.setSpacing(Spacing.SECTION_SPACING)

        # Title
        title = QLabel("Dashboard")
        title.setObjectName("h1")
        self.content_layout.addWidget(title)

        # Summary Cards
        self.summary_layout = QHBoxLayout()
        self.summary_layout.setSpacing(Spacing.SCALE_16)
        self.content_layout.addLayout(self.summary_layout)

        # Charts Row 1
        charts_layout1 = QHBoxLayout()
        charts_layout1.setSpacing(Spacing.SCALE_24)

        self.collection_chart_view = QChartView()
        self.collection_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.collection_chart_view.setMinimumHeight(300)
        charts_layout1.addWidget(self.collection_chart_view, 1)

        self.duration_chart_view = QChartView()
        self.duration_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.duration_chart_view.setMinimumHeight(300)
        charts_layout1.addWidget(self.duration_chart_view, 1)

        self.content_layout.addLayout(charts_layout1)

        # Charts Row 2
        charts_layout2 = QHBoxLayout()
        charts_layout2.setSpacing(Spacing.SCALE_24)

        self.trend_chart_view = QChartView()
        self.trend_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.trend_chart_view.setMinimumHeight(300)
        charts_layout2.addWidget(self.trend_chart_view, 1)

        self.content_layout.addLayout(charts_layout2)

        # Lists Row
        lists_layout = QHBoxLayout()
        lists_layout.setSpacing(Spacing.SCALE_24)

        self.top_ups_layout = QVBoxLayout()
        self.recent_invalid_layout = QVBoxLayout()
        self.recent_unfav_layout = QVBoxLayout()

        lists_layout.addLayout(self.top_ups_layout, 1)
        lists_layout.addLayout(self.recent_invalid_layout, 1)
        lists_layout.addLayout(self.recent_unfav_layout, 1)

        self.content_layout.addLayout(lists_layout)

        self.content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def _create_summary_card(self, title, value):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Color.IVORY.value};
                border: 1px solid {Color.WARM_SAND.value};
                border-radius: {BorderRadius.ROUNDED}px;
                padding: {Spacing.CARD_PADDING}px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"color: {Color.CHARCOAL_WARM.value}; font-size: {Typography.SIZE_BODY_STANDARD}px;"
        )

        value_label = QLabel(str(value))
        value_label.setStyleSheet(
            f"color: {Color.ANTHROPIC_NEAR_BLACK.value}; font-size: {Typography.SIZE_SUB_HEADING_LARGE}px; font-weight: bold;"
        )

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return frame

    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self._clear_layout(item.layout())

    def _create_list_section(self, title, items):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel(title)
        title_label.setStyleSheet(
            f"font-size: {Typography.SIZE_FEATURE_TITLE}px; font-weight: bold;"
        )
        layout.addWidget(title_label)

        if not items:
            empty = QLabel("No data available")
            empty.setStyleSheet(f"color: {Color.CHARCOAL_WARM.value};")
            layout.addWidget(empty)
        else:
            for item in items:
                lbl = QLabel(item)
                lbl.setWordWrap(True)
                layout.addWidget(lbl)

        layout.addStretch()
        return widget

    def refresh_data(self):
        data = stats.get_stats(self.db_conn)

        # Summary Cards
        self._clear_layout(self.summary_layout)
        self.summary_layout.addWidget(
            self._create_summary_card("Total Videos", data.get("total_videos", 0))
        )
        self.summary_layout.addWidget(
            self._create_summary_card(
                "Total Collections", data.get("total_collections", 0)
            )
        )
        self.summary_layout.addWidget(
            self._create_summary_card("Total UPs", data.get("total_ups", 0))
        )
        self.summary_layout.addWidget(
            self._create_summary_card("Following UPs", data.get("following_ups", 0))
        )
        self.summary_layout.addWidget(
            self._create_summary_card("Invalid Videos", data.get("invalid_videos", 0))
        )

        # Collection Chart
        coll_chart = QChart()
        coll_chart.setTitle("Collection Counts")
        coll_chart.setAnimationOptions(QChart.SeriesAnimations)

        if data.get("collection_counts"):
            series = QBarSeries()
            bar_set = QBarSet("Videos")
            categories = []

            # Take top 10
            for item in data["collection_counts"][:10]:
                categories.append(item["name"])
                bar_set.append(item["count"])

            series.append(bar_set)
            coll_chart.addSeries(series)

            axisX = QBarCategoryAxis()
            axisX.append(categories)
            coll_chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)

            axisY = QValueAxis()
            coll_chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)

            coll_chart.legend().setVisible(False)
        self.collection_chart_view.setChart(coll_chart)

        # Duration Chart (Pie)
        dur_chart = QChart()
        dur_chart.setTitle("Duration Distribution")
        dur_chart.setAnimationOptions(QChart.SeriesAnimations)

        dur_series = QPieSeries()
        has_durations = False
        for bucket, count in data.get("duration_distribution", {}).items():
            if count > 0:
                has_durations = True
                dur_series.append(bucket, count)

        if has_durations:
            dur_chart.addSeries(dur_series)
        self.duration_chart_view.setChart(dur_chart)

        # Monthly Trend Chart (Line)
        trend_chart = QChart()
        trend_chart.setTitle("Monthly Trend")
        trend_chart.setAnimationOptions(QChart.SeriesAnimations)

        if data.get("monthly_trend"):
            trend_series = QLineSeries()
            categories = []
            max_val = 0
            for i, item in enumerate(data["monthly_trend"]):
                trend_series.append(i, item["count"])
                categories.append(item["month"])
                max_val = max(max_val, item["count"])

            trend_chart.addSeries(trend_series)

            axisX = QBarCategoryAxis()
            axisX.append(categories)
            trend_chart.addAxis(axisX, Qt.AlignBottom)
            trend_series.attachAxis(axisX)

            axisY = QValueAxis()
            axisY.setRange(0, max_val + (max_val * 0.1))
            trend_chart.addAxis(axisY, Qt.AlignLeft)
            trend_series.attachAxis(axisY)

        self.trend_chart_view.setChart(trend_chart)

        # Lists Row
        self._clear_layout(self.top_ups_layout)
        self._clear_layout(self.recent_invalid_layout)
        self._clear_layout(self.recent_unfav_layout)

        top_ups = [f"{up['name']} ({up['count']})" for up in data.get("top_ups", [])]
        self.top_ups_layout.addWidget(self._create_list_section("Top UPs", top_ups))

        recent_inv = [
            f"{v['title']} (by {v['up_name']})" for v in data.get("recent_invalid", [])
        ]
        self.recent_invalid_layout.addWidget(
            self._create_list_section("Recent Invalid", recent_inv)
        )

        recent_unf = [
            f"{v['title']} (by {v['up_name']})" for v in data.get("recent_unfav", [])
        ]
        self.recent_unfav_layout.addWidget(
            self._create_list_section("Recent Unfavorited", recent_unf)
        )
