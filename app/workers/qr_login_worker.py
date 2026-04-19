from typing import Any, Callable

import qrcode
from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap

from app.services import auth_service, config_service


def build_qr_pixmap(data: str, *, box_size: int = 8, border: int = 2) -> QPixmap:
    """Build a QPixmap QR image from URL/data text."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    matrix = qr.get_matrix()
    side = len(matrix)
    image_size = side * box_size

    image = QImage(image_size, image_size, QImage.Format.Format_RGB32)
    image.fill(QColor("white"))

    painter = QPainter(image)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor("black"))

    for y, row in enumerate(matrix):
        for x, filled in enumerate(row):
            if filled:
                painter.drawRect(x * box_size, y * box_size, box_size, box_size)

    painter.end()
    return QPixmap.fromImage(image)


class QRLoginWorker(QThread):
    qr_ready = Signal(str)
    status_changed = Signal(str)
    login_success = Signal(dict)
    login_failed = Signal(str)

    def __init__(
        self,
        *,
        timeout_seconds: int = 180,
        poll_interval_seconds: int = 2,
        request_timeout: int = 10,
        config_path: str = config_service.DEFAULT_CONFIG_PATH,
        request_get: Callable[..., Any] | None = None,
        time_func: Callable[[], float] | None = None,
        sleep_func: Callable[[float], None] | None = None,
        create_session_func: Callable[..., dict[str, Any]] = auth_service.create_qrcode_login_session,
        poll_session_func: Callable[..., dict[str, Any]] = auth_service.poll_qrcode_login_session,
        verify_cookie_func: Callable[..., auth_service.CookieVerificationResult] = auth_service.verify_cookie_dict,
        load_config_func: Callable[..., tuple[Any, str, dict[str, Any]]] = config_service.load_config,
        save_config_func: Callable[..., dict[str, Any]] = config_service.save_config,
    ) -> None:
        super().__init__()
        self.timeout_seconds = timeout_seconds
        self.poll_interval_seconds = poll_interval_seconds
        self.request_timeout = request_timeout
        self.config_path = config_path

        self._request_get = request_get
        self._time_func = time_func
        self._sleep_func = sleep_func

        self._create_session_func = create_session_func
        self._poll_session_func = poll_session_func
        self._verify_cookie_func = verify_cookie_func
        self._load_config_func = load_config_func
        self._save_config_func = save_config_func

        self._stop_requested = False

    def request_stop(self) -> None:
        self._stop_requested = True

    @staticmethod
    def _build_status_text(code: int, remaining: int) -> str:
        if code == 86101:
            return f"等待扫码... ({remaining}s)"
        if code == 86090:
            return f"已扫码，请在手机上确认登录... ({remaining}s)"
        if code == 0:
            return "已确认登录，正在验证 Cookie..."
        return f"扫码状态更新: {code} ({remaining}s)"

    @staticmethod
    def _build_failure_message(result: dict[str, Any]) -> str:
        status = result.get("status")
        if status == "expired":
            return "二维码已过期，请重新获取。"
        if status == "timeout":
            return "扫码超时，请重新获取二维码。"
        return str(result.get("error") or "扫码登录失败")

    def _call_create_session(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"timeout": self.request_timeout}
        if self._request_get is not None:
            kwargs["request_get"] = self._request_get
        return self._create_session_func(**kwargs)

    def _call_poll_session(self, qrcode_key: str) -> dict[str, Any]:
        def _status_callback(status: dict[str, Any]) -> None:
            if self._stop_requested:
                return
            code = int(status.get("code", -1))
            remaining = int(status.get("remaining", 0))
            self.status_changed.emit(self._build_status_text(code, remaining))

        kwargs: dict[str, Any] = {
            "timeout_seconds": self.timeout_seconds,
            "poll_interval_seconds": self.poll_interval_seconds,
            "request_timeout": self.request_timeout,
            "status_callback": _status_callback,
        }
        if self._request_get is not None:
            kwargs["request_get"] = self._request_get
        if self._time_func is not None:
            kwargs["time_func"] = self._time_func
        if self._sleep_func is not None:
            kwargs["sleep_func"] = self._sleep_func

        return self._poll_session_func(qrcode_key, **kwargs)

    def _call_verify_cookie(
        self, cookie_dict: dict[str, Any]
    ) -> auth_service.CookieVerificationResult:
        kwargs: dict[str, Any] = {
            "timeout": self.request_timeout,
            "require_login": True,
        }
        if self._request_get is not None:
            kwargs["request_get"] = self._request_get
        return self._verify_cookie_func(cookie_dict, **kwargs)

    def run(self) -> None:
        self.status_changed.emit("正在生成登录二维码...")
        create_result = self._call_create_session()

        if not create_result.get("success"):
            self.login_failed.emit(str(create_result.get("error") or "二维码生成失败"))
            return

        qrcode_key = str(create_result["qrcode_key"])
        qrcode_url = str(create_result["qrcode_url"])
        self.qr_ready.emit(qrcode_url)
        self.status_changed.emit("请使用 Bilibili 手机 APP 扫码")

        if self._stop_requested:
            self.login_failed.emit("扫码登录已取消")
            return

        poll_result = self._call_poll_session(qrcode_key)
        if self._stop_requested:
            self.login_failed.emit("扫码登录已取消")
            return

        if not poll_result.get("success"):
            self.login_failed.emit(self._build_failure_message(poll_result))
            return

        cookie_dict = dict(poll_result.get("cookie_dict") or {})
        verify_result = self._call_verify_cookie(cookie_dict)
        if not verify_result.valid:
            message = verify_result.error or "Cookie 验证失败"
            self.login_failed.emit(message)
            return

        uid = cookie_dict.get("DedeUserID")
        if not uid:
            self.login_failed.emit("登录成功但缺少 DedeUserID，无法保存配置")
            return

        try:
            _, _, settings = self._load_config_func(self.config_path)
        except Exception:  # pylint: disable=broad-except
            settings = None

        cookie_str = auth_service.serialize_cookie_dict(cookie_dict)
        try:
            self._save_config_func(
                uid=uid,
                cookie=cookie_str,
                path=self.config_path,
                settings=settings,
            )
        except Exception as exc:  # pylint: disable=broad-except
            self.login_failed.emit(f"保存配置失败: {exc}")
            return

        self.status_changed.emit("扫码登录成功，Cookie 已保存")
        self.login_success.emit(cookie_dict)
