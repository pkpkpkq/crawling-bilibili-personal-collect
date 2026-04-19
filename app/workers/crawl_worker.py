import logging
import re
from typing import Any, Mapping

from PySide6.QtCore import QThread, Signal

from app.services.crawl_service import CrawlService


class _QtLogForwardHandler(logging.Handler):
    def __init__(self, forward_func):
        super().__init__(level=logging.INFO)
        self._forward_func = forward_func
        self.setFormatter(logging.Formatter("%(message)s"))

    def emit(self, record) -> None:
        try:
            message = self.format(record)
        except Exception:  # pylint: disable=broad-except
            message = record.getMessage()
        self._forward_func(message)


class CrawlWorker(QThread):
    """Run crawl service in a background QThread and stream logs/progress."""

    log_message = Signal(str)
    progress_changed = Signal(int, int)
    crawl_completed = Signal(object)
    crawl_error = Signal(str)

    _TOTAL_COLLECTIONS_RE = re.compile(r"开始并发爬取\s*(\d+)\s*个收藏夹")
    _COLLECTION_DONE_PATTERNS = (
        re.compile(r"收藏夹\s+.+\s+完成"),
        re.compile(r"跳过\s+.+"),
        re.compile(r"爬取收藏夹\s+.+\s+时发生错误"),
    )

    def __init__(
        self,
        *,
        uid: Any,
        cookie: str,
        settings: Mapping[str, Any],
        crawl_service: CrawlService | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.uid = uid
        self.cookie = cookie
        self.settings = dict(settings or {})
        self._crawl_service = crawl_service or CrawlService()

        self._stop_requested = False
        self._total_collections = 0
        self._processed_collections = 0

        self._root_logger: logging.Logger | None = None
        self._root_level: int | None = None
        self._log_handler: _QtLogForwardHandler | None = None

    def request_stop(self) -> None:
        self._stop_requested = True
        self.requestInterruption()
        self.log_message.emit("已请求停止，等待当前爬取任务收尾...")

    def _attach_log_bridge(self) -> None:
        root_logger = logging.getLogger()
        self._root_logger = root_logger
        self._root_level = root_logger.level

        if root_logger.level > logging.INFO:
            root_logger.setLevel(logging.INFO)

        handler = _QtLogForwardHandler(self._consume_log_line)
        root_logger.addHandler(handler)
        self._log_handler = handler

    def _detach_log_bridge(self) -> None:
        if self._root_logger is not None and self._log_handler is not None:
            self._root_logger.removeHandler(self._log_handler)

        if self._root_logger is not None and self._root_level is not None:
            self._root_logger.setLevel(self._root_level)

        self._root_logger = None
        self._root_level = None
        self._log_handler = None

    def _consume_log_line(self, message: str) -> None:
        self.log_message.emit(message)

        total_match = self._TOTAL_COLLECTIONS_RE.search(message)
        if total_match:
            self._total_collections = int(total_match.group(1))
            self._processed_collections = 0
            self.progress_changed.emit(0, self._total_collections)
            return

        if self._total_collections <= 0:
            return

        for pattern in self._COLLECTION_DONE_PATTERNS:
            if pattern.search(message):
                if self._processed_collections < self._total_collections:
                    self._processed_collections += 1
                    self.progress_changed.emit(
                        self._processed_collections,
                        self._total_collections,
                    )
                return

    def run(self) -> None:
        if self._stop_requested:
            self.crawl_error.emit("爬取已取消")
            return

        self._attach_log_bridge()
        try:
            result = self._crawl_service.run_headless_crawl(
                uid=self.uid,
                cookie=self.cookie,
                settings=self.settings,
            )
        except Exception as exc:  # pylint: disable=broad-except
            self.crawl_error.emit(str(exc))
        else:
            if (
                result.success
                and self._total_collections > 0
                and self._processed_collections < self._total_collections
            ):
                self._processed_collections = self._total_collections
                self.progress_changed.emit(
                    self._processed_collections,
                    self._total_collections,
                )
            self.crawl_completed.emit(result)
        finally:
            self._detach_log_bridge()
