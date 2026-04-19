from PySide6.QtCore import QObject, QTimer, Signal

from app.services.download_service import QUALITY_MAP
from app.ui.pages.downloads_page import DownloadsPage


class StubPageDownloadService:
    def __init__(self, collections=None, error=None):
        self._collections = list(collections or [])
        self._error = error
        self.calls = []

    def get_latest_collections(self, db_path):
        self.calls.append(db_path)
        if self._error is not None:
            raise self._error
        return [dict(row) for row in self._collections]


class DummyDownloadWorker(QObject):
    status_changed = Signal(str)
    progress_changed = Signal(int, int)
    download_succeeded = Signal(dict)
    download_failed = Signal(dict)
    finished = Signal()

    def __init__(self, *, summary, success=True, status_messages=None, progress_events=None):
        super().__init__()
        self._running = False
        self._summary = dict(summary)
        self._success = success
        self._status_messages = list(status_messages or [])
        self._progress_events = list(progress_events or [])

    def isRunning(self):
        return self._running

    def start(self):
        self._running = True

        def _emit_sequence():
            for message in self._status_messages:
                self.status_changed.emit(message)
            for current, total in self._progress_events:
                self.progress_changed.emit(current, total)

            if self._success:
                self.download_succeeded.emit(dict(self._summary))
            else:
                self.download_failed.emit(dict(self._summary))
            self._running = False
            self.finished.emit()

        QTimer.singleShot(0, _emit_sequence)

    def deleteLater(self):
        return None

    def wait(self, _ms):
        return True


def test_downloads_page_initialization_loads_quality_and_collections(qtbot):
    service = StubPageDownloadService(
        collections=[
            {"id": 101, "name": "收藏夹 A", "active_count": 2},
            {"id": 202, "name": "收藏夹 B", "active_count": 8},
        ]
    )

    page = DownloadsPage(download_service=service, db_path="fixture.db")
    qtbot.addWidget(page)

    qualities = [page.quality_combo.itemData(i) for i in range(page.quality_combo.count())]
    assert qualities == list(QUALITY_MAP.keys())

    assert page.collection_combo.count() == 2
    assert page.collection_combo.itemData(0) == 101
    assert page.collection_combo.itemText(1) == "收藏夹 B (8 个视频)"
    assert page.collections_hint_label.text() == "可下载收藏夹: 2"
    assert service.calls == ["fixture.db"]


def test_downloads_page_single_download_success_updates_summary(qtbot):
    service = StubPageDownloadService(collections=[])
    page = DownloadsPage(download_service=service, db_path="fixture.db")
    qtbot.addWidget(page)

    captured = {}
    worker = DummyDownloadWorker(
        success=True,
        status_messages=["正在下载视频: BV12345"],
        progress_events=[(0, 1), (1, 1)],
        summary={
            "mode": "single",
            "success": True,
            "bv_id": "BV12345",
            "success_count": 1,
            "fail_count": 0,
            "cookie_warning": None,
        },
    )

    def _factory(**kwargs):
        captured.update(kwargs)
        return worker

    page._create_worker = _factory

    page.mode_combo.setCurrentIndex(0)
    page.single_bv_input.setText("12345")
    page.quality_combo.setCurrentText("720p")

    with qtbot.waitSignal(page.download_completed, timeout=2000) as blocker:
        page.start_download()

    qtbot.waitUntil(lambda: page._worker is None, timeout=2000)

    summary = blocker.args[0]
    assert summary["success"] is True
    assert captured["mode"] == "single"
    assert captured["bv_id"] == "12345"
    assert captured["quality"] == "720p"
    assert page.status_label.text() == "状态: 下载完成"
    assert page.progress_label.text() == "进度: 1/1"
    assert "开始单视频下载" in page.log_output.toPlainText()
    assert "[单视频] BV12345 | 成功: 1 失败: 0" in page.log_output.toPlainText()
    assert page.btn_start.isEnabled() is True


def test_downloads_page_missing_ytdlp_failure_shows_install_hint(qtbot):
    service = StubPageDownloadService(collections=[{"id": 7, "name": "Fav A", "active_count": 3}])
    page = DownloadsPage(download_service=service, db_path="fixture.db")
    qtbot.addWidget(page)

    worker = DummyDownloadWorker(
        success=False,
        status_messages=["正在下载收藏夹: 7"],
        progress_events=[(0, 0), (1, 1)],
        summary={
            "mode": "collection",
            "success": False,
            "collection_id": 7,
            "collection_name": "Fav A",
            "success_count": 0,
            "fail_count": 2,
            "skipped_invalid_count": 0,
            "skipped_existing_count": 1,
            "error": {
                "code": "missing_ytdlp",
                "message": "未找到 yt-dlp，请先安装: pip install yt-dlp",
                "details": {"install_url": "https://github.com/yt-dlp/yt-dlp"},
            },
        },
    )
    page._create_worker = lambda **kwargs: worker

    page.mode_combo.setCurrentIndex(1)
    with qtbot.waitSignal(page.download_completed, timeout=2000) as blocker:
        page.start_download()

    qtbot.waitUntil(lambda: page._worker is None, timeout=2000)

    summary = blocker.args[0]
    assert summary["success"] is False
    assert page.status_label.text() == "状态: 缺少 yt-dlp，无法下载"
    logs = page.log_output.toPlainText()
    assert "未找到 yt-dlp，请先安装" in logs
    assert "安装指引: https://github.com/yt-dlp/yt-dlp" in logs
    assert "[收藏夹] Fav A | 成功: 0 失败: 2 跳过失效: 0 跳过已存在: 1" in logs


def test_downloads_page_missing_cookie_warning_is_logged(qtbot):
    service = StubPageDownloadService(collections=[])
    page = DownloadsPage(download_service=service, db_path="fixture.db")
    qtbot.addWidget(page)

    worker = DummyDownloadWorker(
        success=True,
        summary={
            "mode": "single",
            "success": True,
            "bv_id": "BV9ZZ",
            "success_count": 1,
            "fail_count": 0,
            "cookie_warning": {
                "code": "cookie_missing",
                "message": "config.json 中没有 cookie",
            },
        },
    )
    page._create_worker = lambda **kwargs: worker

    page.mode_combo.setCurrentIndex(0)
    page.single_bv_input.setText("BV9ZZ")

    with qtbot.waitSignal(page.download_completed, timeout=2000):
        page.start_download()

    logs = page.log_output.toPlainText()
    assert "Cookie 提示: config.json 中没有 cookie" in logs
    assert page.status_label.text() == "状态: 下载完成"


def test_downloads_page_validation_guards_missing_inputs(qtbot):
    service = StubPageDownloadService(collections=[])
    page = DownloadsPage(download_service=service, db_path="fixture.db")
    qtbot.addWidget(page)

    page._create_worker = lambda **kwargs: (_ for _ in ()).throw(RuntimeError("should not create worker"))

    page.mode_combo.setCurrentIndex(0)
    page.single_bv_input.clear()
    page.start_download()
    assert page.status_label.text() == "状态: 请输入 BV 号"

    page.mode_combo.setCurrentIndex(1)
    page.start_download()
    assert page.status_label.text() == "状态: 请先加载并选择收藏夹"


def test_downloads_page_refresh_collections_failure_sets_error_state(qtbot):
    service = StubPageDownloadService(error=RuntimeError("db is missing"))
    page = DownloadsPage(download_service=service, db_path="fixture.db")
    qtbot.addWidget(page)

    page.refresh_collections()

    assert page.collection_combo.count() == 0
    assert page.collections_hint_label.text() == "可下载收藏夹: 0"
    assert page.status_label.text() == "状态: 收藏夹加载失败"
    assert "收藏夹加载失败: db is missing" in page.log_output.toPlainText()
