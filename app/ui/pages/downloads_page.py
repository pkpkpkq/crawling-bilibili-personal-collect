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
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.repositories.connection import get_db_path
from app.services import config_service
from app.services.download_service import DownloadService, QUALITY_MAP
from app.theme import BorderRadius, Color, Spacing
from app.workers.download_worker import COOKIE_ERROR_CODES, DownloadWorker


class DownloadsPage(QWidget):
    """Desktop download center for single BV and collection jobs."""

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
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
        )
        layout.setSpacing(Spacing.SCALE_16)

        title = QLabel("Download Center")
        title.setObjectName("h1")
        layout.addWidget(title)

        controls_grid = QGridLayout()
        controls_grid.setHorizontalSpacing(Spacing.SCALE_12)
        controls_grid.setVerticalSpacing(Spacing.SCALE_12)

        self.mode_combo = QComboBox()
        self.mode_combo.addItem("下载单个视频（BV）", "single")
        self.mode_combo.addItem("下载整个收藏夹", "collection")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)

        self.quality_combo = QComboBox()
        for quality in QUALITY_MAP:
            self.quality_combo.addItem(quality, quality)

        self.output_input = QLineEdit("downloads")
        self.output_input.setPlaceholderText("下载目录（默认 downloads）")

        controls_grid.addWidget(QLabel("下载模式:"), 0, 0)
        controls_grid.addWidget(self.mode_combo, 0, 1)
        controls_grid.addWidget(QLabel("画质:"), 0, 2)
        controls_grid.addWidget(self.quality_combo, 0, 3)
        controls_grid.addWidget(QLabel("输出目录:"), 1, 0)
        controls_grid.addWidget(self.output_input, 1, 1, 1, 3)

        layout.addLayout(controls_grid)

        self.chk_use_cookie = QCheckBox("使用 config.json 中的 Cookie（推荐）")
        self.chk_use_cookie.setChecked(True)
        layout.addWidget(self.chk_use_cookie)

        self.single_group = QWidget()
        single_layout = QHBoxLayout(self.single_group)
        single_layout.setContentsMargins(0, 0, 0, 0)
        single_layout.setSpacing(Spacing.SCALE_12)

        single_layout.addWidget(QLabel("BV 号:"))
        self.single_bv_input = QLineEdit()
        self.single_bv_input.setPlaceholderText("例如 BV1xx411c7mD（也可不带 BV 前缀）")
        single_layout.addWidget(self.single_bv_input, stretch=1)

        layout.addWidget(self.single_group)

        self.collection_group = QWidget()
        collection_layout = QHBoxLayout(self.collection_group)
        collection_layout.setContentsMargins(0, 0, 0, 0)
        collection_layout.setSpacing(Spacing.SCALE_12)

        collection_layout.addWidget(QLabel("收藏夹:"))
        self.collection_combo = QComboBox()
        self.collection_combo.setMinimumWidth(260)
        collection_layout.addWidget(self.collection_combo, stretch=1)

        self.btn_refresh_collections = QPushButton("刷新收藏夹")
        self.btn_refresh_collections.clicked.connect(self.refresh_collections)
        collection_layout.addWidget(self.btn_refresh_collections)

        self.collections_hint_label = QLabel("可下载收藏夹: 0")
        collection_layout.addWidget(self.collections_hint_label)

        layout.addWidget(self.collection_group)

        button_row = QHBoxLayout()
        button_row.setSpacing(Spacing.SCALE_12)

        self.btn_start = QPushButton("开始下载")
        self.btn_start.clicked.connect(self.start_download)
        button_row.addWidget(self.btn_start)

        self.btn_clear_log = QPushButton("清空日志")
        self.btn_clear_log.clicked.connect(self.clear_logs)
        button_row.addWidget(self.btn_clear_log)

        button_row.addStretch()
        layout.addLayout(button_row)

        self.status_label = QLabel("状态: 空闲")
        self.status_label.setStyleSheet(
            "QLabel {"
            f"border: 1px solid {Color.WARM_SAND.value};"
            f"border-radius: {BorderRadius.ROUNDED}px;"
            f"padding: {Spacing.SCALE_8}px;"
            f"background-color: {Color.IVORY.value};"
            "}"
        )

        self.progress_label = QLabel("进度: 0/0")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)

        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("下载任务日志会显示在这里...")
        layout.addWidget(self.log_output, stretch=1)

        self._on_mode_changed(self.mode_combo.currentIndex())

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
        self.log_output.append(message)

    def _set_status(self, text: str, *, kind: str = "info") -> None:
        color = {
            "info": Color.CHARCOAL_WARM.value,
            "success": Color.TERRACOTTA_BRAND.value,
            "error": Color.ERROR_CRIMSON.value,
        }.get(kind, Color.CHARCOAL_WARM.value)
        self.status_label.setStyleSheet(
            "QLabel {"
            f"border: 1px solid {Color.WARM_SAND.value};"
            f"border-radius: {BorderRadius.ROUNDED}px;"
            f"padding: {Spacing.SCALE_8}px;"
            f"background-color: {Color.IVORY.value};"
            f"color: {color};"
            "}"
        )
        self.status_label.setText(f"状态: {text}")

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
            self.collections_hint_label.setText("可下载收藏夹: 0")
            self._set_status("收藏夹加载失败", kind="error")
            self._append_log(f"收藏夹加载失败: {exc}")
            return

        self.collection_combo.blockSignals(True)
        self.collection_combo.clear()
        for row in rows:
            name = str(row.get("name", "未知收藏夹"))
            active_count = int(row.get("active_count", 0))
            text = f"{name} ({active_count} 个视频)"
            self.collection_combo.addItem(text, int(row.get("id", 0)))
        self.collection_combo.blockSignals(False)

        self.collection_combo.setEnabled(len(rows) > 0 and self._worker is None)
        self.collections_hint_label.setText(f"可下载收藏夹: {len(rows)}")

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
                self._set_status("请输入 BV 号", kind="error")
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
                self._set_status("请先加载并选择收藏夹", kind="error")
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
        self._set_status("下载中...")

        self._set_controls_running(True)
        worker.start()

    @Slot()
    def clear_logs(self) -> None:
        self.log_output.clear()

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
        self._set_status(message, kind="info")

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
        self._set_status("下载完成", kind="success")
        self._append_log(self._format_summary(summary))
        self.download_completed.emit(summary)

    @Slot(dict)
    def _on_download_failed(self, summary: dict[str, Any]) -> None:
        self._append_cookie_warning(summary)
        error = dict(summary.get("error") or {})
        code = str(error.get("code") or "")
        message = str(error.get("message") or "下载失败")

        if code == "missing_ytdlp":
            self._set_status("缺少 yt-dlp，无法下载", kind="error")
            self._append_log(message)
            install_url = (error.get("details") or {}).get("install_url")
            if install_url:
                self._append_log(f"安装指引: {install_url}")
        elif code in COOKIE_ERROR_CODES:
            self._set_status("Cookie 不可用，请先在设置页完成登录", kind="error")
            self._append_log(f"Cookie 错误: {message}")
        else:
            self._set_status("下载失败", kind="error")
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
