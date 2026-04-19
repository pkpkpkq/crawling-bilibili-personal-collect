from PySide6.QtCore import QObject, QTimer, Qt, Signal
from PySide6.QtWidgets import QMessageBox

from app.ui.pages.settings_page import SettingsPage


class DummyQRWorker(QObject):
    qr_ready = Signal(str)
    status_changed = Signal(str)
    login_success = Signal(dict)
    login_failed = Signal(str)
    finished = Signal()

    def __init__(self, *, success=True):
        super().__init__()
        self._running = False
        self._stop_requested = False
        self._success = success

    def isRunning(self):
        return self._running

    def start(self):
        self._running = True

        def _emit_sequence():
            if self._stop_requested:
                self.login_failed.emit("扫码登录已取消")
            else:
                self.qr_ready.emit("https://example.invalid/qr")
                self.status_changed.emit("等待扫码... (120s)")
                if self._success:
                    self.login_success.emit({"SESSDATA": "abc", "DedeUserID": "321"})
                else:
                    self.login_failed.emit("二维码已过期，请重新获取。")
            self._running = False
            self.finished.emit()

        QTimer.singleShot(0, _emit_sequence)

    def request_stop(self):
        self._stop_requested = True

    def deleteLater(self):
        return None

    def wait(self, _ms):
        return True


def test_settings_page_qr_success_updates_cookie_and_status(qtbot, mocker):
    mocker.patch("app.services.config_service.load_config", return_value=("123", "", {}))
    info_box = mocker.patch.object(QMessageBox, "information")
    warning_box = mocker.patch.object(QMessageBox, "warning")

    page = SettingsPage()
    qtbot.addWidget(page)

    worker = DummyQRWorker(success=True)
    page._create_qr_worker = lambda: worker

    with qtbot.waitSignal(page.settings_saved, timeout=2000):
        page.start_qr_login()

    assert "SESSDATA=abc" in page.text_cookie.toPlainText()
    assert page.uid == "321"
    assert page.btn_start_qr.isEnabled() is True
    assert page.btn_cancel_qr.isEnabled() is False
    assert page.qr_status_label.text() == "等待扫码... (120s)"
    pixmap = page.qr_image_label.pixmap()
    assert pixmap is not None and not pixmap.isNull()
    info_box.assert_called_once()
    warning_box.assert_not_called()


def test_settings_page_qr_failure_shows_warning(qtbot, mocker):
    mocker.patch("app.services.config_service.load_config", return_value=("123", "", {}))
    warning_box = mocker.patch.object(QMessageBox, "warning")

    page = SettingsPage()
    qtbot.addWidget(page)

    worker = DummyQRWorker(success=False)
    page._create_qr_worker = lambda: worker

    qtbot.mouseClick(page.btn_start_qr, Qt.MouseButton.LeftButton)
    qtbot.waitUntil(lambda: page._qr_worker is None, timeout=2000)

    assert page.qr_status_label.text() == "二维码已过期，请重新获取。"
    warning_box.assert_called_once()
