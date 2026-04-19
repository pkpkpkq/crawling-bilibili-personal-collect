from PySide6.QtCore import QObject, QTimer, Signal

from app.services.crawl_service import CrawlRunResult
from app.ui.pages.crawl_page import CrawlPage


class DummyCrawlWorker(QObject):
    log_message = Signal(str)
    progress_changed = Signal(int, int)
    crawl_completed = Signal(object)
    crawl_error = Signal(str)
    finished = Signal()

    def __init__(self, *, result, emit_error=None):
        super().__init__()
        self._running = False
        self._result = result
        self._emit_error = emit_error
        self.stop_requested = False

    def isRunning(self):
        return self._running

    def start(self):
        self._running = True

        def _emit_sequence():
            self.log_message.emit("开始并发爬取 2 个收藏夹（2 线程）...")
            self.progress_changed.emit(1, 2)
            self.progress_changed.emit(2, 2)
            if self._emit_error is not None:
                self.crawl_error.emit(self._emit_error)
            self.crawl_completed.emit(self._result)
            self._running = False
            self.finished.emit()

        QTimer.singleShot(0, _emit_sequence)

    def request_stop(self):
        self.stop_requested = True

    def deleteLater(self):
        return None

    def wait(self, _ms):
        return True


def test_crawl_page_start_success_updates_progress_and_stats(qtbot, mocker):
    mocker.patch(
        "app.ui.pages.crawl_page.config_service.load_config",
        return_value=("uid-100", "SESSDATA=ok", {"max_workers_crawl": 2}),
    )

    result = CrawlRunResult(
        success=True,
        duration_seconds=3.2,
        stats={"new": 3, "invalid": 1, "unfav": 2, "total": 12},
    )

    page = CrawlPage()
    qtbot.addWidget(page)

    worker = DummyCrawlWorker(result=result)
    page._create_worker = lambda uid, cookie, settings: worker

    with qtbot.waitSignal(page.crawl_completed, timeout=2000) as blocker:
        page.start_crawl()

    assert blocker.args[0].success is True
    assert page.status_label.text() == "状态: 爬取完成"
    assert page.progress_label.text() == "进度: 2/2"
    assert page.progress_bar.maximum() == 2
    assert page.progress_bar.value() == 2
    assert page.stat_total_label.text() == "总视频: 12"
    assert page.stat_new_label.text() == "新增: 3"
    assert page.stat_invalid_label.text() == "失效: 1"
    assert page.stat_unfav_label.text() == "取消收藏: 2"
    assert "开始执行爬取任务" in page.log_output.toPlainText()
    assert page.btn_start.isEnabled() is True
    assert page.btn_stop.isEnabled() is False


def test_crawl_page_handles_failed_result_and_error_signal(qtbot, mocker):
    mocker.patch(
        "app.ui.pages.crawl_page.config_service.load_config",
        return_value=("uid-100", "SESSDATA=ok", {}),
    )

    result = CrawlRunResult(
        success=False,
        duration_seconds=0,
        stats={"new": 0, "invalid": 0, "unfav": 0, "total": 0},
        error="boom",
    )

    page = CrawlPage()
    qtbot.addWidget(page)

    worker = DummyCrawlWorker(result=result, emit_error="thread issue")
    page._create_worker = lambda uid, cookie, settings: worker

    with qtbot.waitSignal(page.crawl_completed, timeout=2000):
        page.start_crawl()

    logs = page.log_output.toPlainText()
    assert page.status_label.text() == "状态: 爬取失败"
    assert "爬取线程异常: thread issue" in logs
    assert "爬取失败: boom" in logs


def test_crawl_page_stop_requests_worker_stop(qtbot, mocker):
    mocker.patch(
        "app.ui.pages.crawl_page.config_service.load_config",
        return_value=("uid-100", "SESSDATA=ok", {}),
    )

    result = CrawlRunResult(
        success=True,
        duration_seconds=1.0,
        stats={"new": 0, "invalid": 0, "unfav": 0, "total": 0},
    )

    page = CrawlPage()
    qtbot.addWidget(page)

    worker = DummyCrawlWorker(result=result)
    page._create_worker = lambda uid, cookie, settings: worker

    page.start_crawl()
    assert page.btn_stop.isEnabled() is True

    page.stop_crawl()
    assert worker.stop_requested is True
    assert page.status_label.text() == "状态: 停止请求中..."

    qtbot.waitUntil(lambda: page._worker is None, timeout=2000)


def test_crawl_page_config_load_failure_keeps_idle(qtbot, mocker):
    mocker.patch(
        "app.ui.pages.crawl_page.config_service.load_config",
        side_effect=RuntimeError("missing config"),
    )

    page = CrawlPage()
    qtbot.addWidget(page)

    page.start_crawl()

    assert page._worker is None
    assert page.status_label.text() == "状态: 配置加载失败"
    assert "配置加载失败: missing config" in page.log_output.toPlainText()
