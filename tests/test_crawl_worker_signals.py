import logging

from app.services.crawl_service import CrawlRunResult
from app.workers.crawl_worker import CrawlWorker


class DummyCrawlService:
    def __init__(self):
        self.called_with = None

    def run_headless_crawl(self, uid, cookie, settings):
        self.called_with = {
            "uid": uid,
            "cookie": cookie,
            "settings": settings,
        }

        logging.info("开始并发爬取 2 个收藏夹（2 线程）...")
        logging.info("收藏夹 A 完成: 1 条, 新增 1, 失效 0, 取消收藏 0")
        logging.info("跳过 B（media_count 和 mtime 均无变化）")

        return CrawlRunResult(
            success=True,
            duration_seconds=2.5,
            stats={"new": 1, "invalid": 0, "unfav": 0, "total": 10},
        )


def test_crawl_worker_emits_logs_progress_and_completion(qtbot):
    service = DummyCrawlService()
    worker = CrawlWorker(
        uid="uid-1",
        cookie="SESSDATA=abc",
        settings={"max_workers_crawl": 2},
        crawl_service=service,
    )

    logs = []
    progress = []
    worker.log_message.connect(logs.append)
    worker.progress_changed.connect(lambda current, total: progress.append((current, total)))

    with qtbot.waitSignal(worker.crawl_completed, timeout=2000) as blocker:
        worker.start()

    worker.wait(1000)

    result = blocker.args[0]
    assert result.success is True
    assert service.called_with == {
        "uid": "uid-1",
        "cookie": "SESSDATA=abc",
        "settings": {"max_workers_crawl": 2},
    }

    assert any("开始并发爬取 2 个收藏夹" in message for message in logs)
    assert (0, 2) in progress
    assert progress[-1] == (2, 2)


class FailingCrawlService:
    def run_headless_crawl(self, uid, cookie, settings):
        raise RuntimeError("worker boom")


def test_crawl_worker_emits_error_when_service_raises(qtbot):
    worker = CrawlWorker(
        uid="uid-err",
        cookie="",
        settings={},
        crawl_service=FailingCrawlService(),
    )

    with qtbot.waitSignal(worker.crawl_error, timeout=2000) as blocker:
        worker.start()

    worker.wait(1000)

    assert blocker.args == ["worker boom"]
