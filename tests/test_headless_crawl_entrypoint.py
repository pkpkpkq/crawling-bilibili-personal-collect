import main

from app.services.crawl_service import CrawlRunResult


class DummyCrawlService:
    def __init__(self):
        self.called_with = None

    def run_headless_crawl(self, uid, cookie, settings):
        self.called_with = {"uid": uid, "cookie": cookie, "settings": settings}
        return CrawlRunResult(
            success=True,
            duration_seconds=1.0,
            stats={"new": 1, "invalid": 0, "unfav": 0, "total": 1},
        )


def test_run_headless_delegates_to_crawl_service(monkeypatch):
    service = DummyCrawlService()
    monkeypatch.setattr(
        main,
        "load_config",
        lambda: ("uid-100", "SESSDATA=aaa", {"max_workers_crawl": 4}),
    )
    monkeypatch.setattr(main, "CrawlService", lambda: service)

    result = main.run_headless()

    assert service.called_with == {
        "uid": "uid-100",
        "cookie": "SESSDATA=aaa",
        "settings": {"max_workers_crawl": 4},
    }
    assert result.success is True


def test_main_returns_zero_when_headless_crawl_succeeds(monkeypatch):
    monkeypatch.setattr(main, "configure_logging", lambda: None)
    monkeypatch.setattr(
        main,
        "run_headless",
        lambda: CrawlRunResult(
            success=True,
            duration_seconds=1.0,
            stats={"new": 0, "invalid": 0, "unfav": 0, "total": 0},
        ),
    )

    assert main.main() == 0


def test_main_returns_non_zero_when_headless_crawl_fails(monkeypatch):
    monkeypatch.setattr(main, "configure_logging", lambda: None)
    monkeypatch.setattr(
        main,
        "run_headless",
        lambda: CrawlRunResult(
            success=False,
            duration_seconds=0,
            stats={"new": 0, "invalid": 0, "unfav": 0, "total": 0},
            error="boom",
        ),
    )

    assert main.main() == 1
