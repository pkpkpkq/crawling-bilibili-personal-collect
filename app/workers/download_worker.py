from __future__ import annotations

from typing import Any

from PySide6.QtCore import QThread, Signal

from app.repositories.connection import get_db_path
from app.services.download_service import DownloadService

COOKIE_ERROR_CODES = {
    "config_missing",
    "config_invalid_json",
    "cookie_missing",
    "cookie_export_failed",
}


class DownloadWorker(QThread):
    """Run single/collection download jobs in a background QThread."""

    status_changed = Signal(str)
    progress_changed = Signal(int, int)
    download_succeeded = Signal(dict)
    download_failed = Signal(dict)

    def __init__(
        self,
        *,
        mode: str,
        quality: str = "best",
        output_base: str = "downloads",
        bv_id: str | None = None,
        collection_id: int | None = None,
        db_path: str | None = None,
        config_path: str = "config.json",
        use_cookie: bool = True,
        download_service: DownloadService | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.mode = mode
        self.quality = quality
        self.output_base = output_base or "downloads"
        self.bv_id = bv_id
        self.collection_id = collection_id
        self.db_path = db_path or get_db_path()
        self.config_path = config_path
        self.use_cookie = use_cookie
        self._download_service = download_service or DownloadService()

    @staticmethod
    def _normalize_bv_id(raw_value: str | None) -> str:
        value = str(raw_value or "").strip()
        if not value:
            return ""
        if value.upper().startswith("BV"):
            return f"BV{value[2:]}"
        return f"BV{value}"

    def _build_summary(self, **kwargs) -> dict[str, Any]:
        summary = {
            "mode": self.mode,
            "quality": self.quality,
            "output_base": self.output_base,
            "success": False,
            "success_count": 0,
            "fail_count": 0,
            "skipped_invalid_count": 0,
            "skipped_existing_count": 0,
            "cookie_warning": None,
            "error": None,
        }
        summary.update(kwargs)
        return summary

    def _emit_failed(self, summary: dict[str, Any]) -> None:
        summary["success"] = False
        self.download_failed.emit(summary)

    def _run_single(self, cookie_file: str | None, cookie_warning: dict[str, Any] | None) -> None:
        normalized_bv = self._normalize_bv_id(self.bv_id)
        if not normalized_bv:
            self._emit_failed(
                self._build_summary(
                    mode="single",
                    bv_id="",
                    fail_count=1,
                    cookie_warning=cookie_warning,
                    error={"code": "invalid_input", "message": "BV 号不能为空"},
                )
            )
            return

        self.status_changed.emit(f"正在下载视频: {normalized_bv}")
        self.progress_changed.emit(0, 1)

        result = self._download_service.download_video(
            normalized_bv,
            self.output_base,
            cookie_file=cookie_file,
            quality=self.quality,
        )

        summary = self._build_summary(
            mode="single",
            bv_id=normalized_bv,
            output_dir=result.get("output_dir", self.output_base),
            success=bool(result.get("success")),
            success_count=1 if result.get("success") else 0,
            fail_count=0 if result.get("success") else 1,
            cookie_warning=cookie_warning,
            error=result.get("error"),
        )

        self.progress_changed.emit(1, 1)

        if summary["success"]:
            self.download_succeeded.emit(summary)
        else:
            self._emit_failed(summary)


    def _run_collection(self, cookie_file: str | None, cookie_warning: dict[str, Any] | None) -> None:
        if self.collection_id is None:
            self._emit_failed(
                self._build_summary(
                    mode="collection",
                    collection_id=None,
                    cookie_warning=cookie_warning,
                    error={"code": "invalid_input", "message": "缺少收藏夹 ID"},
                )
            )
            return

        self.status_changed.emit(f"正在下载收藏夹: {self.collection_id}")
        self.progress_changed.emit(0, 0)

        result = self._download_service.download_collection(
            db_path=self.db_path,
            collection_id=int(self.collection_id),
            output_base=self.output_base,
            quality=self.quality,
            cookie_file=cookie_file,
        )

        summary = self._build_summary(
            mode="collection",
            collection_id=int(self.collection_id),
            collection_name=result.get("collection_name"),
            output_dir=result.get("output_dir"),
            success=bool(result.get("success")),
            success_count=int(result.get("success_count", 0)),
            fail_count=int(result.get("fail_count", 0)),
            skipped_invalid_count=int(result.get("skipped_invalid_count", 0)),
            skipped_existing_count=int(result.get("skipped_existing_count", 0)),
            cookie_warning=cookie_warning,
            error=result.get("error"),
        )

        self.progress_changed.emit(1, 1)

        if summary["success"]:
            self.download_succeeded.emit(summary)
        else:
            self._emit_failed(summary)

    def _prepare_cookie(self) -> tuple[str | None, dict[str, Any] | None, dict[str, Any] | None]:
        if not self.use_cookie:
            return None, None, None

        self.status_changed.emit("正在准备 Cookie...")
        cookie_result = self._download_service.export_cookies_for_ytdlp(self.config_path)
        if cookie_result.get("success"):
            return cookie_result.get("cookie_file"), None, None

        error = cookie_result.get("error") or {
            "code": "cookie_export_failed",
            "message": "Cookie 导出失败",
        }

        if str(error.get("code") or "") in COOKIE_ERROR_CODES:
            return None, error, None

        return None, None, error

    def run(self) -> None:
        try:
            self.status_changed.emit("准备下载任务...")
            cookie_file, cookie_warning, cookie_error = self._prepare_cookie()

            if cookie_warning is not None:
                warning_text = str(cookie_warning.get("message") or "Cookie 不可用")
                self.status_changed.emit(f"Cookie 不可用，将尝试无 Cookie 下载: {warning_text}")

            if cookie_error is not None:
                fail_count = 1 if self.mode == "single" else 0
                self._emit_failed(
                    self._build_summary(
                        mode=self.mode,
                        bv_id=self._normalize_bv_id(self.bv_id),
                        collection_id=self.collection_id,
                        fail_count=fail_count,
                        cookie_warning=cookie_warning,
                        error=cookie_error,
                    )
                )
                return

            if self.mode == "single":
                self._run_single(cookie_file, cookie_warning)
                return

            if self.mode == "collection":
                self._run_collection(cookie_file, cookie_warning)
                return

            self._emit_failed(
                self._build_summary(
                    mode=self.mode,
                    fail_count=1,
                    cookie_warning=cookie_warning,
                    error={
                        "code": "invalid_mode",
                        "message": f"未知下载模式: {self.mode}",
                    },
                )
            )
        except Exception as exc:  # pylint: disable=broad-except
            self._emit_failed(
                self._build_summary(
                    mode=self.mode,
                    bv_id=self._normalize_bv_id(self.bv_id),
                    collection_id=self.collection_id,
                    fail_count=1 if self.mode == "single" else 0,
                    error={
                        "code": "worker_exception",
                        "message": f"下载线程异常: {exc}",
                    },
                )
            )
