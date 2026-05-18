from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from app.repositories.connection import get_db_path
from app.services import config_service
from app.services.download_service import DownloadService, QUALITY_MAP
from app.theme import Spacing
from app.ui import strings
from app.ui.components import LogPanel, PageHeader, StatusBadge, SurfaceCard
from app.workers.download_worker import COOKIE_ERROR_CODES, DownloadWorker


class DownloadsPage(QWidget):

    download_completed = Signal(dict)

    def __init__(
        self,
        *,
        download_service: DownloadService | None = None,
        db_path: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._download_service = download_service or DownloadService()
        self._db_path = db_path or get_db_path()
        self._worker: DownloadWorker | None = None

        self._setup_ui()
        self.refresh_collections()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            Spacing.PAGE_MARGIN,
            Spacing.PAGE_MARGIN,
            Spacing.PAGE_MARGIN,
            Spacing.PAGE_MARGIN,
        )
        layout.setSpacing(Spacing.SCALE_16)

        self._page_header = PageHeader(strings.PAGE_TITLE_DOWNLOAD_CENTER)
        layout.addWidget(self._page_header)

        controls_card = SurfaceCard()
        controls_grid = QGridLayout()
        controls_grid.setHorizontalSpacing(Spacing.SCALE_12)
        controls_grid.setVerticalSpacing(Spacing.SCALE_12)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem(strings.DL_MODE_SINGLE, "single")
        self.mode_combo.addItem(strings.DL_MODE_COLLECTION, "collection")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)

        self.quality_combo = QComboBox()
        for quality in QUALITY_MAP:
            self.quality_combo.addItem(quality, quality)

        self.output_input = QLineEdit("downloads")
        self.output_input.setPlaceholderText(strings.DL_OUTPUT_PLACEHOLDER)

        controls_grid.addWidget(QLabel(strings.DL_MODE_LABEL), 0, 0)
        controls_grid.addWidget(self.mode_combo, 0, 1)
        controls_grid.addWidget(QLabel(strings.DL_QUALITY_LABEL), 0, 2)
        controls_grid.addWidget(self.quality_combo, 0, 3)
        controls_grid.addWidget(QLabel(strings.DL_OUTPUT_LABEL), 1, 0)
        controls_grid.addWidget(self.output_input, 1, 1, 1, 3)
        controls_grid.setColumnStretch(4, 1)

        controls_card.card_layout.addLayout(controls_grid)

        self.chk_use_cookie = QCheckBox(strings.DL_USE_COOKIE)
        self.chk_use_cookie.setChecked(True)
        controls_card.card_layout.addWidget(self.chk_use_cookie)

        layout.addWidget(controls_card)

        target_card = SurfaceCard()

        self.single_group = QWidget()
        single_layout = QHBoxLayout(self.single_group)
        single_layout.setContentsMargins(0, 0, 0, 0)
        single_layout.setSpacing(Spacing.SCALE_12)

        single_layout.addWidget(QLabel(strings.DL_BV_LABEL))
        self.single_bv_input = QLineEdit()
        self.single_bv_input.setPlaceholderText(strings.DL_BV_PLACEHOLDER)
        self.single_bv_input.setMinimumWidth(260)
        single_layout.addWidget(self.single_bv_input)
        single_layout.addStretch()

        target_card.card_layout.addWidget(self.single_group)

        self.collection_group = QWidget()
        collection_layout = QHBoxLayout(self.collection_group)
        collection_layout.setContentsMargins(0, 0, 0, 0)
        collection_layout.setSpacing(Spacing.SCALE_12)

        collection_layout.addWidget(QLabel(strings.DL_COLLECTION_LABEL))
        self.collection_combo = QComboBox()
        self.collection_combo.setMinimumWidth(260)
        collection_layout.addWidget(self.collection_combo)

        self.btn_refresh_collections = QPushButton(strings.BTN_REFRESH_COLLECTIONS)
        self.btn_refresh_collections.clicked.connect(self.refresh_collections)
        collection_layout.addWidget(self.btn_refresh_collections)

        self.collections_hint_label = QLabel(
            strings.DL_COLLECTIONS_AVAILABLE.format(count=0)
        )
        collection_layout.addWidget(self.collections_hint_label)
        collection_layout.addStretch()

        target_card.card_layout.addWidget(self.collection_group)

        layout.addWidget(target_card)

        button_row = QHBoxLayout()
        button_row.setSpacing(Spacing.SCALE_12)

        self.btn_start = QPushButton(strings.BTN_START_DOWNLOAD)
        self.btn_start.clicked.connect(self.start_download)
        button_row.addWidget(self.btn_start)

        self.btn_clear_log = QPushButton(strings.BTN_CLEAR_LOG)
        self.btn_clear_log.clicked.connect(self.clear_logs)
        button_row.addWidget(self.btn_clear_log)

        button_row.addStretch()
        layout.addLayout(button_row)

        status_card = SurfaceCard()
        status_row = QHBoxLayout()
        status_row.setSpacing(Spacing.SCALE_12)

        self.status_label = StatusBadge(strings.DOWNLOAD_STATUS_IDLE, "info")
        status_row.addWidget(self.status_label)

        self.progress_label = QLabel("进度: 0/0")
        status_row.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        status_row.addWidget(self.progress_bar, stretch=1)

        status_card.card_layout.addLayout(status_row)
        layout.addWidget(status_card)

        self._log_panel = LogPanel()
        self._log_panel.text_edit.setPlaceholderText(
            strings.DL_DOWNLOAD_LOG_PLACEHOLDER
        )
        layout.addWidget(self._log_panel, stretch=1)

        self._on_mode_changed(self.mode_combo.currentIndex())

    @property
    def log_output(self):
        return self._log_panel.text_edit

    def _set_controls_running(self, running: bool) -> None:
        self.btn_start.setEnabled(not running)
        self.mode_combo.setEnabled(not running)
        self.quality_combo.setEnabled(not running)
        self.output_input.setEnabled(not running)
        self.single_bv_input.setEnabled(not running)
        self.collection_combo.setEnabled((not running) and self.collection_combo.count() > 0)
        self.btn_refresh_collections.setEnabled(not running)
        self.chk_use_cookie.setEnabled(not running)

    def _append_log(self, message: str) -> None:
        self._log_panel.append_log(message)

    def _create_worker(self, **kwargs: Any) -> DownloadWorker:
        return DownloadWorker(
            download_service=self._download_service,
            db_path=self._db_path,
            config_path=config_service.DEFAULT_CONFIG_PATH,
            **kwargs,
        )

    @Slot()
    def refresh_collections(self) -> None:
        try:
            rows = self._download_service.get_latest_collections(self._db_path)
        except Exception as exc:  # pylint: disable=broad-except
            self.collection_combo.clear()
            self.collection_combo.setEnabled(False)
            self.collections_hint_label.setText(
                strings.DL_COLLECTIONS_AVAILABLE.format(count=0)
            )
            self.status_label.set_status("状态: 收藏夹加载失败", kind="error")
            self._append_log(f"收藏夹加载失败: {exc}")
            return

        self.collection_combo.blockSignals(True)
        self.collection_combo.clear()
        for row in rows:
            name = str(row.get("name", "未知收藏夹"))
            active_count = int(row.get("active_count", 0))
            text = strings.COLLECTION_VIDEO_COUNT.format(name=name, count=active_count)
            self.collection_combo.addItem(text, int(row.get("id", 0)))
        self.collection_combo.blockSignals(False)

        self.collection_combo.setEnabled(len(rows) > 0 and self._worker is None)
        self.collections_hint_label.setText(
            strings.DL_COLLECTIONS_AVAILABLE.format(count=len(rows))
        )

        if not rows:
            self._append_log("未找到可下载收藏夹，请先执行爬取。")

    @Slot(int)
    def _on_mode_changed(self, _index: int) -> None:
        mode = str(self.mode_combo.currentData())
        single_mode = mode == "single"
        self.single_group.setVisible(single_mode)
        self.collection_group.setVisible(not single_mode)

    @Slot()
    def start_download(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return

        mode = str(self.mode_combo.currentData())
        quality = str(self.quality_combo.currentData() or "best")
        output_base = self.output_input.text().strip() or "downloads"
        use_cookie = self.chk_use_cookie.isChecked()

        if mode == "single":
            bv_id = self.single_bv_input.text().strip()
            if not bv_id:
                self.status_label.set_status("状态: 请输入 BV 号", kind="error")
                return

            worker = self._create_worker(
                mode="single",
                bv_id=bv_id,
                quality=quality,
                output_base=output_base,
                use_cookie=use_cookie,
            )
            self._append_log(f"开始单视频下载: {bv_id} (画质: {quality})")
        else:
            collection_id = self.collection_combo.currentData()
            if collection_id is None:
                self.status_label.set_status("状态: 请先加载并选择收藏夹", kind="error")
                return

            worker = self._create_worker(
                mode="collection",
                collection_id=int(collection_id),
                quality=quality,
                output_base=output_base,
                use_cookie=use_cookie,
            )
            self._append_log(
                f"开始收藏夹下载: {self.collection_combo.currentText()} (画质: {quality})"
            )

        self._worker = worker
        worker.status_changed.connect(self._on_status_changed)
        worker.progress_changed.connect(self._on_progress_changed)
        worker.download_succeeded.connect(self._on_download_succeeded)
        worker.download_failed.connect(self._on_download_failed)
        worker.finished.connect(self._on_worker_finished)

        self.progress_label.setText("进度: 0/0")
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.status_label.set_status(strings.DOWNLOAD_STATUS_DOWNLOADING, kind="info")

        self._set_controls_running(True)
        worker.start()

    @Slot()
    def clear_logs(self) -> None:
        self._log_panel.clear_logs()
        self.status_label.set_status(strings.DOWNLOAD_STATUS_IDLE, kind="info")

    @staticmethod
    def _format_summary(summary: dict[str, Any]) -> str:
        mode = str(summary.get("mode", "unknown"))
        if mode == "single":
            bv_id = summary.get("bv_id") or "未知 BV"
            return (
                f"[单视频] {bv_id} | 成功: {int(summary.get('success_count', 0))} "
                f"失败: {int(summary.get('fail_count', 0))}"
            )

        name = (
            summary.get("collection_name")
            or summary.get("collection_id")
            or "未知收藏夹"
        )
        return (
            f"[收藏夹] {name} | 成功: {int(summary.get('success_count', 0))} "
            f"失败: {int(summary.get('fail_count', 0))} "
            f"跳过失效: {int(summary.get('skipped_invalid_count', 0))} "
            f"跳过已存在: {int(summary.get('skipped_existing_count', 0))}"
        )

    def _append_cookie_warning(self, summary: dict[str, Any]) -> None:
        warning = dict(summary.get("cookie_warning") or {})
        if not warning:
            return
        message = str(warning.get("message") or "Cookie 不可用")
        self._append_log(f"Cookie 提示: {message}")

    @Slot(str)
    def _on_status_changed(self, message: str) -> None:
        self.status_label.set_status(f"状态: {message}", kind="info")

    @Slot(int, int)
    def _on_progress_changed(self, current: int, total: int) -> None:
        if total <= 0:
            self.progress_bar.setRange(0, 0)
            self.progress_label.setText("进度: 准备中...")
            return

        safe_current = max(0, min(current, total))
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(safe_current)
        self.progress_label.setText(f"进度: {safe_current}/{total}")

    @Slot(dict)
    def _on_download_succeeded(self, summary: dict[str, Any]) -> None:
        self._append_cookie_warning(summary)
        self.status_label.set_status(strings.DOWNLOAD_STATUS_COMPLETE, kind="success")
        self._append_log(self._format_summary(summary))
        self.download_completed.emit(summary)

    @Slot(dict)
    def _on_download_failed(self, summary: dict[str, Any]) -> None:
        self._append_cookie_warning(summary)
        error = dict(summary.get("error") or {})
        code = str(error.get("code") or "")
        message = str(error.get("message") or "下载失败")

        if code == "missing_ytdlp":
            self.status_label.set_status("状态: 缺少 yt-dlp，无法下载", kind="error")
            self._append_log(message)
            install_url = (error.get("details") or {}).get("install_url")
            if install_url:
                self._append_log(f"安装指引: {install_url}")
        elif code in COOKIE_ERROR_CODES:
            self.status_label.set_status("状态: Cookie 不可用，请先在设置页完成登录", kind="error")
            self._append_log(f"Cookie 错误: {message}")
        else:
            self.status_label.set_status(strings.DOWNLOAD_STATUS_FAILED, kind="error")
            self._append_log(message)

        self._append_log(self._format_summary(summary))
        self.download_completed.emit(summary)

    @Slot()
    def _on_worker_finished(self) -> None:
        self._set_controls_running(False)
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None

    def closeEvent(self, event) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._worker.wait(1000)
        super().closeEvent(event)
