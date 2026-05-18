from typing import Any, Mapping

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from app.services import config_service
from app.theme import Spacing
from app.ui import strings
from app.ui.components import LogPanel, PageHeader, StatusBadge, SurfaceCard
from app.workers.crawl_worker import CrawlWorker


class CrawlPage(QWidget):
    crawl_completed = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._worker: CrawlWorker | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            Spacing.PAGE_MARGIN,
            Spacing.PAGE_MARGIN,
            Spacing.PAGE_MARGIN,
            Spacing.PAGE_MARGIN,
        )
        layout.setSpacing(Spacing.SCALE_16)

        self._page_header = PageHeader(strings.PAGE_TITLE_CRAWL_CENTER)
        layout.addWidget(self._page_header)

        action_card = SurfaceCard()
        button_row = QHBoxLayout()
        button_row.setSpacing(Spacing.SCALE_12)

        self.btn_start = QPushButton(strings.BTN_START_CRAWL)
        self.btn_start.clicked.connect(self.start_crawl)
        button_row.addWidget(self.btn_start)

        self.btn_stop = QPushButton(strings.BTN_STOP)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.stop_crawl)
        button_row.addWidget(self.btn_stop)

        self.btn_clear_log = QPushButton(strings.BTN_CLEAR_LOG)
        self.btn_clear_log.clicked.connect(self.clear_logs)
        button_row.addWidget(self.btn_clear_log)

        button_row.addStretch()
        action_card.card_layout.addLayout(button_row)

        status_row = QHBoxLayout()
        status_row.setSpacing(Spacing.SCALE_12)

        self.status_label = StatusBadge(strings.CRAWL_STATUS_IDLE, "info")
        status_row.addWidget(self.status_label)

        self.progress_label = QLabel("进度: 0/0")
        status_row.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        status_row.addWidget(self.progress_bar, stretch=1)

        action_card.card_layout.addLayout(status_row)

        layout.addWidget(action_card)

        stats_card = SurfaceCard()
        stats_grid = QGridLayout()
        stats_grid.setHorizontalSpacing(Spacing.SCALE_16)
        stats_grid.setVerticalSpacing(Spacing.SCALE_8)

        self.stat_total_label = QLabel(strings.CRAWL_STAT_TOTAL)
        self.stat_new_label = QLabel(strings.CRAWL_STAT_NEW)
        self.stat_invalid_label = QLabel(strings.CRAWL_STAT_INVALID)
        self.stat_unfav_label = QLabel(strings.CRAWL_STAT_UNFAV)
        self.stat_duration_label = QLabel(strings.CRAWL_STAT_DURATION)

        stats_grid.addWidget(self.stat_total_label, 0, 0)
        stats_grid.addWidget(self.stat_new_label, 0, 1)
        stats_grid.addWidget(self.stat_invalid_label, 1, 0)
        stats_grid.addWidget(self.stat_unfav_label, 1, 1)
        stats_grid.addWidget(self.stat_duration_label, 2, 0, 1, 2)
        stats_card.card_layout.addLayout(stats_grid)

        layout.addWidget(stats_card)

        self._log_panel = LogPanel()
        self._log_panel.text_edit.setPlaceholderText(
            strings.DL_CRAWL_LOG_PLACEHOLDER
        )
        layout.addWidget(self._log_panel, stretch=1)

    @property
    def log_output(self):
        return self._log_panel.text_edit

    def _create_worker(self, uid: Any, cookie: str, settings: Mapping[str, Any]) -> CrawlWorker:
        return CrawlWorker(uid=uid, cookie=cookie, settings=settings)

    def _set_controls_running(self, running: bool) -> None:
        self.btn_start.setEnabled(not running)
        self.btn_stop.setEnabled(running)

    def _append_log(self, message: str) -> None:
        self._log_panel.append_log(message)

    def _update_summary_labels(self, stats: Mapping[str, Any], duration_seconds: float) -> None:
        self.stat_total_label.setText(f"总视频: {int(stats.get('total', 0))}")
        self.stat_new_label.setText(f"新增: {int(stats.get('new', 0))}")
        self.stat_invalid_label.setText(f"失效: {int(stats.get('invalid', 0))}")
        self.stat_unfav_label.setText(f"取消收藏: {int(stats.get('unfav', 0))}")
        self.stat_duration_label.setText(f"耗时: {float(duration_seconds):.2f}s")

    @Slot()
    def start_crawl(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return

        try:
            uid, cookie, settings = config_service.load_config()
        except Exception as exc:  # pylint: disable=broad-except
            self.status_label.set_status(strings.CRAWL_STATUS_CONFIG_ERROR, "error")
            self._append_log(f"配置加载失败: {exc}")
            return

        self.status_label.set_status(strings.CRAWL_STATUS_RUNNING, "info")
        self.progress_label.setText("进度: 0/0")
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self._update_summary_labels({}, 0.0)
        self._append_log("开始执行爬取任务...")

        worker = self._create_worker(uid, cookie, settings)
        self._worker = worker

        worker.log_message.connect(self._append_log)
        worker.progress_changed.connect(self._on_progress_changed)
        worker.crawl_completed.connect(self._on_crawl_completed)
        worker.crawl_error.connect(self._on_crawl_error)
        worker.finished.connect(self._on_worker_finished)

        self._set_controls_running(True)
        worker.start()

    @Slot()
    def stop_crawl(self) -> None:
        if self._worker is None or not self._worker.isRunning():
            return

        self.status_label.set_status(strings.CRAWL_STATUS_STOPPING, "info")
        self.btn_stop.setEnabled(False)
        self._worker.request_stop()

    @Slot()
    def clear_logs(self) -> None:
        self._log_panel.clear_logs()
        self.status_label.set_status(strings.CRAWL_STATUS_IDLE, "info")

    @Slot(int, int)
    def _on_progress_changed(self, current: int, total: int) -> None:
        if total <= 0:
            self.progress_bar.setRange(0, 0)
            self.progress_label.setText("进度: 0/0")
            return

        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(max(0, min(current, total)))
        self.progress_label.setText(f"进度: {current}/{total}")

    @Slot(object)
    def _on_crawl_completed(self, result) -> None:
        success = bool(getattr(result, "success", False))
        duration_seconds = float(getattr(result, "duration_seconds", 0.0) or 0.0)
        stats = dict(getattr(result, "stats", {}) or {})
        error = getattr(result, "error", None)

        if success:
            self.status_label.set_status(strings.CRAWL_STATUS_COMPLETE, "success")
            self._append_log("爬取任务完成")
        else:
            self.status_label.set_status(strings.CRAWL_STATUS_FAILED, "error")
            if error:
                self._append_log(f"爬取失败: {error}")

        self._update_summary_labels(stats, duration_seconds)
        self.crawl_completed.emit(result)

    @Slot(str)
    def _on_crawl_error(self, message: str) -> None:
        self.status_label.set_status(strings.CRAWL_STATUS_FAILED, "error")
        self._append_log(f"爬取线程异常: {message}")

    @Slot()
    def _on_worker_finished(self) -> None:
        self._set_controls_running(False)
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None

    def closeEvent(self, event) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.request_stop()
            self._worker.wait(1000)
        super().closeEvent(event)
