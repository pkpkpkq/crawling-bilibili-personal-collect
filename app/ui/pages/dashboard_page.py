from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter, QFont, QColor
from PySide6.QtCharts import (
    QChart,
    QChartView,
    QPieSeries,
    QStackedBarSeries,
    QBarSet,
    QBarCategoryAxis,
    QValueAxis,
    QLineSeries,
)
from app.theme import Color, Typography, Spacing, CHART_PALETTE
from app.repositories import stats
from app.ui import strings
from app.ui.components.page_header import PageHeader
from app.ui.components.summary_card import SummaryCard
from app.ui.components.surface_card import SurfaceCard
from app.ui.components.empty_state import EmptyState


# ── Chart label helpers ──────────────────────────────────────────────


def _axis_label_font() -> QFont:
    f = QFont(Typography.FONT_FAMILY_SANS)
    f.setPixelSize(Typography.SIZE_MICRO)
    return f


_DURATION_SHORT_MAP = {
    "分钟": "分",
    "小时": "时",
}


def _chart_title_font() -> QFont:
    f = QFont(Typography.FONT_FAMILY_SERIF)
    f.setPixelSize(Typography.SIZE_SUB_HEADING_SMALL)
    f.setWeight(QFont.Weight.Medium)
    return f


def _shorten_duration(label: str) -> str:
    for full, short in _DURATION_SHORT_MAP.items():
        label = label.replace(full, short)
    return label


def _shorten_month(month_str: str) -> str:
    """Shorten '2023-10' → '10月', '2025年1月' → '1月'."""
    if "年" in month_str:
        return month_str.split("年")[-1].replace("月", "") + "月"
    if "-" in month_str:
        return month_str.split("-")[-1] + "月"
    return month_str


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
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.verticalScrollBar().setSingleStep(20)

        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setContentsMargins(
            Spacing.PAGE_MARGIN,
            Spacing.PAGE_MARGIN,
            Spacing.PAGE_MARGIN,
            Spacing.PAGE_MARGIN,
        )
        self.content_layout.setSpacing(Spacing.SCALE_32)

        self._header = PageHeader(strings.PAGE_TITLE_DATA_OVERVIEW)
        self.content_layout.addWidget(self._header)

        self.summary_layout = QHBoxLayout()
        self.summary_layout.setSpacing(Spacing.SCALE_16)
        self.content_layout.addLayout(self.summary_layout)

        charts_layout1 = QHBoxLayout()
        charts_layout1.setSpacing(Spacing.SCALE_24)

        self.collection_chart_view = QChartView()
        self.collection_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.collection_chart_view.setMinimumHeight(220)
        charts_layout1.addWidget(self.collection_chart_view, 1)

        self.duration_chart_view = QChartView()
        self.duration_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.duration_chart_view.setMinimumHeight(220)
        charts_layout1.addWidget(self.duration_chart_view, 1)

        self.content_layout.addLayout(charts_layout1)

        charts_layout2 = QHBoxLayout()
        charts_layout2.setSpacing(Spacing.SCALE_24)

        self.trend_chart_view = QChartView()
        self.trend_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.trend_chart_view.setMinimumHeight(220)
        charts_layout2.addWidget(self.trend_chart_view, 1)

        self.content_layout.addLayout(charts_layout2)

        # Insight Cards Row
        self.insight_layout = QHBoxLayout()
        self.insight_layout.setSpacing(Spacing.SCALE_24)
        self.content_layout.addLayout(self.insight_layout)

        self.content_layout.addStretch()

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self._clear_layout(item.layout())

    def _build_insight_card(self, title_text, items):
        card = SurfaceCard()

        title_label = QLabel(title_text)
        title_font = QFont()
        title_font.setWeight(QFont.Weight.Medium)
        title_font.setPixelSize(Typography.SIZE_FEATURE_TITLE)
        title_label.setFont(title_font)
        title_label.setObjectName("h2")
        card.card_layout.addWidget(title_label)

        if not items:
            empty = EmptyState(strings.EMPTY_NO_DATA)
            card.card_layout.addWidget(empty)
        else:
            for item in items:
                lbl = QLabel(item)
                lbl.setWordWrap(True)
                card.card_layout.addWidget(lbl)

        card.card_layout.addStretch()
        return card

    def _apply_chart_theme(self, chart: QChart):
        chart.setBackgroundVisible(False)
        chart.setTitleFont(_chart_title_font())
        chart.setTitleBrush(QColor(Color.CHARCOAL_WARM.value))

        legend = chart.legend()
        if legend and legend.isAttachedToChart():
            _legend_font = QFont(Typography.FONT_FAMILY_SANS)
            _legend_font.setPixelSize(Typography.SIZE_LABEL)
            legend.setFont(_legend_font)
            legend.setLabelBrush(QColor(Color.CHARCOAL_WARM.value))

        for axis in chart.axes():
            axis.setLabelsFont(_axis_label_font())
            axis.setLabelsBrush(QColor(Color.OLIVE_GRAY.value))
            axis.setGridLineColor(QColor(Color.BORDER_CREAM.value))

    def refresh_data(self):
        data = stats.get_stats(self.db_conn)

        # ── KPI Row: SummaryCards ──────────────────────────────────────
        self._clear_layout(self.summary_layout)

        kpi_defs = [
            (strings.SUMMARY_TOTAL_VIDEOS, data.get("total_videos", 0)),
            (strings.SUMMARY_TOTAL_COLLECTIONS, data.get("total_collections", 0)),
            (strings.SUMMARY_TOTAL_UPS, data.get("total_ups", 0)),
            (strings.SUMMARY_FOLLOWING_UPS, data.get("following_ups", 0)),
            (strings.SUMMARY_INVALID_VIDEOS, data.get("invalid_videos", 0)),
        ]
        for title, value in kpi_defs:
            card = SummaryCard(title, str(value))
            self.summary_layout.addWidget(card, 1)

        # ── Collection Distribution (Stacked Bar) ─────────────────────────
        coll_chart = QChart()
        coll_chart.setTitle(strings.CHART_COLLECTION_DISTRIBUTION)
        coll_chart.setAnimationOptions(QChart.SeriesAnimations)

        if data.get("collection_counts"):
            items = data["collection_counts"][:10]
            categories = [item["name"] for item in items]
            n = len(categories)

            series = QStackedBarSeries()
            for i, item in enumerate(items):
                bar_set = QBarSet(item["name"])
                bar_set.setColor(QColor(CHART_PALETTE[i % len(CHART_PALETTE)]))
                bar_set.setBorderColor(QColor(Color.IVORY.value))
                values = [0] * n
                values[i] = item["count"]
                for v in values:
                    bar_set.append(v)
                series.append(bar_set)

            coll_chart.addSeries(series)

            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            axis_x.setLabelsAngle(-45)
            coll_chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            series.attachAxis(axis_x)

            axis_y = QValueAxis()
            axis_y.setLabelFormat("%d")
            coll_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            series.attachAxis(axis_y)

            coll_chart.legend().setVisible(False)

        self._apply_chart_theme(coll_chart)
        self.collection_chart_view.setChart(coll_chart)

        # ── Duration Distribution (Pie) ────────────────────────────────
        dur_chart = QChart()
        dur_chart.setTitle(strings.CHART_DURATION_DISTRIBUTION)
        dur_chart.setAnimationOptions(QChart.SeriesAnimations)

        dur_series = QPieSeries()
        has_durations = False
        for bucket, count in data.get("duration_distribution", {}).items():
            if count > 0:
                has_durations = True
                dur_series.append(_shorten_duration(bucket), count)

        if has_durations:
            dur_chart.addSeries(dur_series)
            for i, slice_ in enumerate(dur_series.slices()):
                color = CHART_PALETTE[i % len(CHART_PALETTE)]
                slice_.setColor(QColor(color))
                slice_.setBorderColor(QColor(Color.IVORY.value))
                # Show label on hover
                slice_.hovered.connect(
                    lambda state, s=slice_: self._on_pie_hover(s, state)
                )

            dur_chart.legend().setAlignment(Qt.AlignmentFlag.AlignBottom)
        dur_chart.layout().setContentsMargins(0, 0, 0, 0)
        dur_chart.setBackgroundRoundness(0)

        self._apply_chart_theme(dur_chart)
        self.duration_chart_view.setChart(dur_chart)

        # ── Monthly Trend (Line) ───────────────────────────────────────
        trend_chart = QChart()
        trend_chart.setTitle(strings.CHART_MONTHLY_TREND)
        trend_chart.setAnimationOptions(QChart.SeriesAnimations)

        if data.get("monthly_trend"):
            trend_series = QLineSeries()
            categories = []
            max_val = 0
            for i, item in enumerate(data["monthly_trend"]):
                trend_series.append(i, item["count"])
                categories.append(_shorten_month(item["month"]))
                max_val = max(max_val, item["count"])

            pen = trend_series.pen()
            pen.setColor(QColor(CHART_PALETTE[0]))
            pen.setWidth(2)
            trend_series.setPen(pen)

            trend_chart.addSeries(trend_series)

            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            axis_x.setLabelsAngle(0)
            trend_chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
            trend_series.attachAxis(axis_x)

            axis_y = QValueAxis()
            axis_y.setRange(0, max_val + (max_val * 0.1 if max_val else 1))
            axis_y.setLabelFormat("%d")
            trend_chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
            trend_series.attachAxis(axis_y)

            trend_chart.legend().hide()

            # Show value on hover via tooltip
            trend_series.hovered.connect(
                lambda point, state: self._on_line_hover(point, state, categories)
            )
        self._apply_chart_theme(trend_chart)
        self.trend_chart_view.setChart(trend_chart)

        # ── Insight Cards Row ──────────────────────────────────────────
        self._clear_layout(self.insight_layout)

        top_ups = [f"{up['name']} ({up['count']})" for up in data.get("top_ups", [])]
        self.insight_layout.addWidget(
            self._build_insight_card(strings.LIST_TOP_UPS, top_ups), 1
        )

        recent_inv = [
            f"{v['title']}" + (f" (by {v['up_name']})" if v.get("up_name") else "")
            for v in data.get("recent_invalid", [])
        ]
        self.insight_layout.addWidget(
            self._build_insight_card(strings.LIST_RECENT_INVALID, recent_inv), 1
        )

        recent_unf = [
            f"{v['title']}" + (f" (by {v['up_name']})" if v.get("up_name") else "")
            for v in data.get("recent_unfav", [])
        ]
        self.insight_layout.addWidget(
            self._build_insight_card(strings.LIST_RECENT_UNFAV, recent_unf), 1
        )

    def _on_pie_hover(self, slice_, state):
        """Show label and explode pie slice on hover."""
        slice_.setExploded(state)
        slice_.setLabelVisible(state)
        if state:
            pct = slice_.percentage() * 100
            slice_.setLabel(f"{slice_.label()}: {int(slice_.value())} ({pct:.1f}%)")

    def _on_line_hover(self, point, state, categories):
        """Show tooltip on line chart hover."""
        from PySide6.QtWidgets import QToolTip
        from PySide6.QtGui import QCursor
        if state:
            idx = int(round(point.x()))
            month = categories[idx] if 0 <= idx < len(categories) else ""
            QToolTip.showText(
                QCursor.pos(),
                f"{month}: {int(point.y())} 个视频",
            )
        else:
            QToolTip.hideText()
