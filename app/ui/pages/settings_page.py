from typing import Any

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.services import auth_service, config_service
from app.theme import Spacing
from app.ui import strings
from app.ui.components import PageHeader, StatusBadge, SurfaceCard
from app.workers.qr_login_worker import QRLoginWorker, build_qr_pixmap


class SettingsPage(QWidget):
    settings_saved = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.uid: Any = None
        self._qr_worker: QRLoginWorker | None = None
        self._setup_ui()
        self.load_current_config()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.verticalScrollBar().setSingleStep(20)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(
            Spacing.PAGE_MARGIN,
            Spacing.PAGE_MARGIN,
            Spacing.PAGE_MARGIN,
            Spacing.PAGE_MARGIN,
        )
        layout.setSpacing(Spacing.SCALE_16)

        self._page_header = PageHeader(strings.PAGE_TITLE_SETTINGS)
        layout.addWidget(self._page_header)

        sync_card = SurfaceCard()
        sync_title = QLabel("同步设置")
        sync_title.setObjectName("h2")
        sync_card.card_layout.addWidget(sync_title)
        form_layout = QFormLayout()
        form_layout.setSpacing(Spacing.SCALE_12)

        self.spin_max_workers_crawl = QSpinBox()
        self.spin_max_workers_crawl.setFixedWidth(120)
        self.spin_max_workers_crawl.setRange(1, 100)
        self.spin_max_workers_crawl.setToolTip(
            "\u722c\u53d6\u6536\u85cf\u5939\u6570\u636e\u65f6\u7684\u6700\u5927\u5e76\u53d1\u7ebf\u7a0b\u6570\u3002\n"
            "\u503c\u8d8a\u5927\u901f\u5ea6\u8d8a\u5feb\uff0c\u4f46\u8fc7\u9ad8\u53ef\u80fd\u89e6\u53d1B\u7ad9\u98ce\u63a7\u3002\u5efa\u8bae 3~10\u3002"
        )
        form_layout.addRow(strings.SETTINGS_CRAWL_CONCURRENCY, self.spin_max_workers_crawl)

        self.spin_max_workers_image = QSpinBox()
        self.spin_max_workers_image.setFixedWidth(120)
        self.spin_max_workers_image.setRange(1, 100)
        self.spin_max_workers_image.setToolTip(
            "\u4e0b\u8f7d\u89c6\u9891\u5c01\u9762\u56fe\u7247\u65f6\u7684\u6700\u5927\u5e76\u53d1\u7ebf\u7a0b\u6570\u3002\n"
            "\u5c01\u9762\u4e0b\u8f7d\u5bf9B\u7ad9\u98ce\u63a7\u5f71\u54cd\u8f83\u5c0f\uff0c\u53ef\u9002\u5f53\u8c03\u9ad8\u3002\u5efa\u8bae 5~20\u3002"
        )
        form_layout.addRow(strings.SETTINGS_IMAGE_CONCURRENCY, self.spin_max_workers_image)

        self.spin_page_delay = QDoubleSpinBox()
        self.spin_page_delay.setFixedWidth(120)
        self.spin_page_delay.setRange(0.0, 10.0)
        self.spin_page_delay.setSingleStep(0.1)
        self.spin_page_delay.setToolTip(
            "\u722c\u53d6\u6bcf\u4e00\u9875\u6536\u85cf\u5939\u540e\u7684\u7b49\u5f85\u65f6\u95f4\uff08\u79d2\uff09\u3002\n"
            "\u7528\u4e8e\u907f\u514d\u8bf7\u6c42\u8fc7\u4e8e\u9891\u7e41\u88abB\u7ad9\u9650\u6d41\u3002\u5efa\u8bae 0.3~1.0 \u79d2\u3002"
        )
        form_layout.addRow(strings.SETTINGS_PAGE_DELAY, self.spin_page_delay)

        self.spin_image_retry = QSpinBox()
        self.spin_image_retry.setFixedWidth(120)
        self.spin_image_retry.setRange(0, 10)
        self.spin_image_retry.setToolTip(
            "\u5c01\u9762\u56fe\u7247\u4e0b\u8f7d\u5931\u8d25\u540e\u7684\u91cd\u8bd5\u6b21\u6570\u3002\n"
            "\u7f51\u7edc\u4e0d\u7a33\u5b9a\u65f6\u53ef\u9002\u5f53\u589e\u52a0\u3002\u5efa\u8bae 2~5 \u6b21\u3002"
        )
        form_layout.addRow(strings.SETTINGS_IMAGE_RETRY, self.spin_image_retry)

        self.spin_backup_keep_count = QSpinBox()
        self.spin_backup_keep_count.setFixedWidth(120)
        self.spin_backup_keep_count.setRange(0, 100)
        self.spin_backup_keep_count.setToolTip(
            "\u6570\u636e\u5e93\u81ea\u52a8\u5907\u4efd\u4fdd\u7559\u7684\u6700\u5927\u4efd\u6570\u3002\n"
            "\u8d85\u51fa\u6b64\u6570\u91cf\u7684\u65e7\u5907\u4efd\u4f1a\u88ab\u81ea\u52a8\u5220\u9664\u3002\u8bbe\u4e3a 0 \u5219\u4e0d\u4fdd\u7559\u5907\u4efd\u3002"
        )
        form_layout.addRow(strings.SETTINGS_BACKUP_KEEP, self.spin_backup_keep_count)

        self.chk_enable_incremental = QCheckBox(strings.SETTINGS_INCREMENTAL_SYNC)
        self.chk_enable_incremental.setToolTip(
            "\u542f\u7528\u540e\uff0c\u6bcf\u6b21\u722c\u53d6\u53ea\u83b7\u53d6\u4e0a\u6b21\u722c\u53d6\u4ee5\u6765\u7684\u65b0\u589e/\u53d8\u66f4\u6570\u636e\uff0c\n"
            "\u663e\u8457\u51cf\u5c11\u722c\u53d6\u65f6\u95f4\u548cAPI\u8bf7\u6c42\u91cf\u3002\n"
            "\u5173\u95ed\u5219\u6bcf\u6b21\u5168\u91cf\u722c\u53d6\u6240\u6709\u6536\u85cf\u5939\u3002"
        )
        form_layout.addRow("", self.chk_enable_incremental)

        sync_card.card_layout.addLayout(form_layout)
        layout.addWidget(sync_card)

        cookie_card = SurfaceCard()
        cookie_title = QLabel("Cookie 认证")
        cookie_title.setObjectName("h2")
        cookie_card.card_layout.addWidget(cookie_title)

        cookie_label = QLabel(strings.LABEL_MANUAL_COOKIE)
        cookie_label.setToolTip(
            "\u4ece\u6d4f\u89c8\u5668\u4e2d\u590d\u5236B\u7ad9\u767b\u5f55Cookie\uff0c\u7c98\u8d34\u5230\u4e0b\u65b9\u6587\u672c\u6846\u3002\n"
            "\u9700\u8981\u5305\u542b SESSDATA \u548c DedeUserID \u5b57\u6bb5\u3002"
        )
        cookie_card.card_layout.addWidget(cookie_label)

        self._cookie_toggle = QPushButton("展开 Cookie 编辑")
        self._cookie_toggle.setObjectName("secondary-btn")
        self._cookie_toggle.clicked.connect(self._toggle_cookie_editor)
        cookie_card.card_layout.addWidget(self._cookie_toggle)

        self.text_cookie = QTextEdit()
        self.text_cookie.setAcceptRichText(False)
        self.text_cookie.setPlaceholderText(strings.DL_COOKIE_PLACEHOLDER)
        self.text_cookie.setMinimumHeight(80)
        self.text_cookie.setMaximumHeight(120)
        self.text_cookie.setVisible(False)
        cookie_card.card_layout.addWidget(self.text_cookie)

        layout.addWidget(cookie_card)

        qr_card = SurfaceCard()
        qr_title = QLabel("扫码登录")
        qr_title.setObjectName("h2")
        qr_card.card_layout.addWidget(qr_title)

        qr_label = QLabel(strings.LABEL_QR_LOGIN)
        qr_label.setToolTip(
            "\u4f7f\u7528B\u7ad9\u624b\u673aAPP\u626b\u63cf\u4e8c\u7ef4\u7801\u5373\u53ef\u81ea\u52a8\u83b7\u53d6Cookie\uff0c\n"
            "\u65e0\u9700\u624b\u52a8\u4ece\u6d4f\u89c8\u5668\u590d\u5236\u3002"
        )
        qr_card.card_layout.addWidget(qr_label)

        self.qr_image_label = QLabel(strings.QR_CLICK_TO_GENERATE)
        self.qr_image_label.setWordWrap(True)
        self.qr_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_image_label.setMinimumSize(180, 180)
        self.qr_image_label.setMaximumSize(220, 220)
        self.qr_image_label.setVisible(True)
        qr_card.card_layout.addWidget(self.qr_image_label)

        self._qr_status_badge = StatusBadge(strings.QR_STATUS_LOADING, "info")
        self._qr_status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._qr_status_badge.setMinimumSize(180, 180)
        self._qr_status_badge.setMaximumSize(220, 220)
        self._qr_status_badge.setVisible(False)
        qr_card.card_layout.addWidget(self._qr_status_badge)

        self.qr_status_label = QLabel(strings.QR_STATUS_READY)
        self.qr_status_label.setWordWrap(True)
        qr_card.card_layout.addWidget(self.qr_status_label)

        qr_button_layout = QHBoxLayout()
        qr_button_layout.setSpacing(Spacing.SCALE_12)

        self.btn_start_qr = QPushButton(strings.BTN_GET_QR)
        self.btn_start_qr.setToolTip(
            "\u751f\u6210B\u7ad9\u626b\u7801\u767b\u5f55\u7684\u4e8c\u7ef4\u7801\uff0c\n"
            "\u7528B\u7ad9\u624b\u673aAPP\u626b\u63cf\u5373\u53ef\u81ea\u52a8\u767b\u5f55\u3002"
        )
        self.btn_start_qr.clicked.connect(self.start_qr_login)
        qr_button_layout.addWidget(self.btn_start_qr)

        self.btn_cancel_qr = QPushButton(strings.BTN_CANCEL_QR)
        self.btn_cancel_qr.setObjectName("secondary-btn")
        self.btn_cancel_qr.clicked.connect(self.cancel_qr_login)
        self.btn_cancel_qr.setEnabled(False)
        qr_button_layout.addWidget(self.btn_cancel_qr)

        qr_card.card_layout.addLayout(qr_button_layout)

        layout.addWidget(qr_card)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.btn_save = QPushButton(strings.BTN_SAVE_SETTINGS)
        self.btn_save.setToolTip("\u5c06\u5f53\u524d\u6240\u6709\u8bbe\u7f6e\u9879\u4fdd\u5b58\u5230\u914d\u7f6e\u6587\u4ef6\u3002")
        self.btn_save.clicked.connect(self.save_settings)
        self.btn_save.setMinimumWidth(160)
        btn_layout.addWidget(self.btn_save)
        
        layout.addLayout(btn_layout)

        scroll_area.setWidget(content_widget)
        outer.addWidget(scroll_area)

    def _set_qr_controls_running(self, running: bool) -> None:
        self.btn_start_qr.setEnabled(not running)
        self.btn_cancel_qr.setEnabled(running)

    def _create_qr_worker(self) -> QRLoginWorker:
        return QRLoginWorker()

    def _toggle_cookie_editor(self) -> None:
        visible = not self.text_cookie.isVisible()
        self.text_cookie.setVisible(visible)
        self._cookie_toggle.setText("收起 Cookie 编辑" if visible else "展开 Cookie 编辑")

    def load_current_config(self) -> None:
        try:
            uid, cookie, settings = config_service.load_config()
            self.uid = uid
            self.text_cookie.setPlainText(cookie)

            self.spin_max_workers_crawl.setValue(settings.get("max_workers_crawl", 3))
            self.spin_max_workers_image.setValue(settings.get("max_workers_image", 10))
            self.spin_page_delay.setValue(settings.get("page_delay", 0.3))
            self.spin_image_retry.setValue(settings.get("image_retry", 3))
            self.spin_backup_keep_count.setValue(settings.get("backup_keep_count", 5))
            self.chk_enable_incremental.setChecked(
                settings.get("enable_incremental", True)
            )
        except Exception:
            pass

    @Slot()
    def save_settings(self) -> None:
        cookie_input = self.text_cookie.toPlainText().strip()
        if cookie_input:
            parsed = auth_service.parse_manual_cookie_input(cookie_input)
            if not parsed.get("success", False):
                missing = ", ".join(parsed.get("missing_fields", []))
                QMessageBox.warning(
                    self, "Cookie \u65e0\u6548", f"Cookie \u7f3a\u5c11\u5fc5\u8981\u5b57\u6bb5: {missing}"
                )
                return

        settings = {
            "max_workers_crawl": self.spin_max_workers_crawl.value(),
            "max_workers_image": self.spin_max_workers_image.value(),
            "page_delay": self.spin_page_delay.value(),
            "image_retry": self.spin_image_retry.value(),
            "backup_keep_count": self.spin_backup_keep_count.value(),
            "enable_incremental": self.chk_enable_incremental.isChecked(),
        }

        try:
            config_service.save_config(
                uid=self.uid or "unknown", cookie=cookie_input, settings=settings
            )
            QMessageBox.information(self, "\u6210\u529f", "\u8bbe\u7f6e\u5df2\u4fdd\u5b58\u3002")
            self.settings_saved.emit()
        except Exception as e:
            QMessageBox.critical(self, "\u9519\u8bef", f"\u4fdd\u5b58\u8bbe\u7f6e\u5931\u8d25: {e}")

    @Slot()
    def start_qr_login(self) -> None:
        if self._qr_worker is not None and self._qr_worker.isRunning():
            return

        self.qr_image_label.setPixmap(QPixmap())
        self.qr_image_label.setVisible(False)
        self._qr_status_badge.set_status(strings.QR_STATUS_LOADING, "info")
        self._qr_status_badge.setVisible(True)
        self.qr_status_label.setText(strings.QR_STATUS_INITIALIZING)

        worker = self._create_qr_worker()
        self._qr_worker = worker

        worker.qr_ready.connect(self._on_qr_ready)
        worker.status_changed.connect(self._on_qr_status_changed)
        worker.login_success.connect(self._on_qr_login_success)
        worker.login_failed.connect(self._on_qr_login_failed)
        worker.finished.connect(self._on_qr_worker_finished)

        self._set_qr_controls_running(True)
        worker.start()

    @Slot()
    def cancel_qr_login(self) -> None:
        if self._qr_worker is None or not self._qr_worker.isRunning():
            return

        self._qr_worker.request_stop()
        self.qr_status_label.setText(strings.QR_STATUS_CANCELLING)
        self.btn_cancel_qr.setEnabled(False)

    @Slot(str)
    def _on_qr_ready(self, qrcode_url: str) -> None:
        pixmap = build_qr_pixmap(qrcode_url)
        self.qr_image_label.setPixmap(
            pixmap.scaled(
                self.qr_image_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )
        self.qr_image_label.setText("")
        self.qr_image_label.setVisible(True)
        self._qr_status_badge.setVisible(False)

    @Slot(str)
    def _on_qr_status_changed(self, message: str) -> None:
        self.qr_status_label.setText(message)

    @Slot(dict)
    def _on_qr_login_success(self, cookie_dict: dict[str, Any]) -> None:
        self.uid = cookie_dict.get("DedeUserID", self.uid)
        self.text_cookie.setPlainText(auth_service.serialize_cookie_dict(cookie_dict))
        QMessageBox.information(self, "\u6210\u529f", "\u626b\u7801\u767b\u5f55\u6210\u529f\uff0cCookie \u5df2\u4fdd\u5b58\u3002")
        self.settings_saved.emit()

    @Slot(str)
    def _on_qr_login_failed(self, message: str) -> None:
        self.qr_image_label.setVisible(False)
        self._qr_status_badge.set_status(message, "error")
        self._qr_status_badge.setVisible(True)
        self.qr_status_label.setText(message)
        QMessageBox.warning(self, "\u626b\u7801\u767b\u5f55\u5931\u8d25", message)

    @Slot()
    def _on_qr_worker_finished(self) -> None:
        self._set_qr_controls_running(False)
        if self._qr_worker is not None:
            self._qr_worker.deleteLater()
            self._qr_worker = None

    def closeEvent(self, event) -> None:
        if self._qr_worker is not None and self._qr_worker.isRunning():
            self._qr_worker.request_stop()
            self._qr_worker.wait(1000)
        super().closeEvent(event)
