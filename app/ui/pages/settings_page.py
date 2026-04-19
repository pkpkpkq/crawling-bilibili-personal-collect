from typing import Any

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.services import auth_service, config_service
from app.theme import BorderRadius, Color, Spacing
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
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
        )
        layout.setSpacing(Spacing.SCALE_16)

        title = QLabel("Settings")
        title.setObjectName("h1")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(Spacing.SCALE_12)

        self.spin_max_workers_crawl = QSpinBox()
        self.spin_max_workers_crawl.setRange(1, 100)
        form_layout.addRow("Max Workers (Crawl):", self.spin_max_workers_crawl)

        self.spin_max_workers_image = QSpinBox()
        self.spin_max_workers_image.setRange(1, 100)
        form_layout.addRow("Max Workers (Image):", self.spin_max_workers_image)

        self.spin_page_delay = QDoubleSpinBox()
        self.spin_page_delay.setRange(0.0, 10.0)
        self.spin_page_delay.setSingleStep(0.1)
        form_layout.addRow("Page Delay (s):", self.spin_page_delay)

        self.spin_image_retry = QSpinBox()
        self.spin_image_retry.setRange(0, 10)
        form_layout.addRow("Image Retry Count:", self.spin_image_retry)

        self.spin_backup_keep_count = QSpinBox()
        self.spin_backup_keep_count.setRange(0, 100)
        form_layout.addRow("Backup Keep Count:", self.spin_backup_keep_count)

        self.chk_enable_incremental = QCheckBox("Enable Incremental Sync")
        form_layout.addRow("", self.chk_enable_incremental)

        layout.addLayout(form_layout)

        layout.addWidget(QLabel("Manual Cookie:"))
        self.text_cookie = QTextEdit()
        self.text_cookie.setAcceptRichText(False)
        self.text_cookie.setPlaceholderText(
            "Paste your SESSDATA and DedeUserID cookie string here..."
        )
        layout.addWidget(self.text_cookie)

        layout.addWidget(QLabel("QR Login:"))

        self.qr_image_label = QLabel("Click \"Get QR Login Code\" to generate QR code")
        self.qr_image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_image_label.setMinimumSize(220, 220)
        self.qr_image_label.setStyleSheet(
            "QLabel {"
            f"background-color: {Color.IVORY.value};"
            f"border: 1px solid {Color.WARM_SAND.value};"
            f"border-radius: {BorderRadius.ROUNDED}px;"
            f"padding: {Spacing.SCALE_8}px;"
            "}"
        )
        layout.addWidget(self.qr_image_label)

        self.qr_status_label = QLabel("Ready")
        self.qr_status_label.setWordWrap(True)
        layout.addWidget(self.qr_status_label)

        qr_button_layout = QHBoxLayout()
        qr_button_layout.setSpacing(Spacing.SCALE_12)

        self.btn_start_qr = QPushButton("Get QR Login Code")
        self.btn_start_qr.clicked.connect(self.start_qr_login)
        qr_button_layout.addWidget(self.btn_start_qr)

        self.btn_cancel_qr = QPushButton("Cancel QR Login")
        self.btn_cancel_qr.clicked.connect(self.cancel_qr_login)
        self.btn_cancel_qr.setEnabled(False)
        qr_button_layout.addWidget(self.btn_cancel_qr)

        layout.addLayout(qr_button_layout)

        self.btn_save = QPushButton("Save Settings")
        self.btn_save.clicked.connect(self.save_settings)
        layout.addWidget(self.btn_save)

    def _set_qr_controls_running(self, running: bool) -> None:
        self.btn_start_qr.setEnabled(not running)
        self.btn_cancel_qr.setEnabled(running)

    def _create_qr_worker(self) -> QRLoginWorker:
        return QRLoginWorker()

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
                    self, "Invalid Cookie", f"Cookie missing required fields: {missing}"
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
            QMessageBox.information(self, "Success", "Settings saved successfully.")
            self.settings_saved.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")


    @Slot()
    def start_qr_login(self) -> None:
        if self._qr_worker is not None and self._qr_worker.isRunning():
            return

        self.qr_image_label.setPixmap(QPixmap())
        self.qr_image_label.setText("Loading QR code...")
        self.qr_status_label.setText("Initializing QR login...")

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
        self.qr_status_label.setText("Cancelling QR login...")
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

    @Slot(str)
    def _on_qr_status_changed(self, message: str) -> None:
        self.qr_status_label.setText(message)

    @Slot(dict)
    def _on_qr_login_success(self, cookie_dict: dict[str, Any]) -> None:
        self.uid = cookie_dict.get("DedeUserID", self.uid)
        self.text_cookie.setPlainText(auth_service.serialize_cookie_dict(cookie_dict))
        QMessageBox.information(self, "Success", "QR login succeeded and cookie saved.")
        self.settings_saved.emit()

    @Slot(str)
    def _on_qr_login_failed(self, message: str) -> None:
        self.qr_status_label.setText(message)
        QMessageBox.warning(self, "QR Login Failed", message)

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
