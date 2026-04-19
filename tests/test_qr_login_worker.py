from app.services.auth_service import CookieVerificationResult
from app.workers.qr_login_worker import QRLoginWorker, build_qr_pixmap


def test_build_qr_pixmap_returns_non_empty_pixmap(qapp):
    pixmap = build_qr_pixmap("https://example.invalid/qr-login")

    assert not pixmap.isNull()
    assert pixmap.width() > 0
    assert pixmap.height() > 0


def test_qr_login_worker_success_persists_cookie_and_emits_signals(qtbot):
    state = {
        "saved": None,
        "verify_called": False,
        "statuses": [],
    }

    def fake_create_session(**kwargs):
        return {
            "success": True,
            "qrcode_key": "key-123",
            "qrcode_url": "https://example.invalid/qr",
        }

    def fake_poll_session(qrcode_key, **kwargs):
        assert qrcode_key == "key-123"
        status_callback = kwargs["status_callback"]
        status_callback({"code": 86101, "remaining": 170})
        status_callback({"code": 86090, "remaining": 140})
        return {
            "success": True,
            "status": "success",
            "cookie_dict": {"SESSDATA": "sess-abc", "DedeUserID": "24680"},
        }

    def fake_verify_cookie(cookie_dict, **kwargs):
        state["verify_called"] = True
        assert cookie_dict["SESSDATA"] == "sess-abc"
        return CookieVerificationResult(valid=True, uname="tester", mid=24680)

    def fake_load_config(path):
        assert path == "config.json"
        return "old-uid", "old-cookie", {"max_workers_crawl": 8}

    def fake_save_config(**kwargs):
        state["saved"] = kwargs
        return kwargs

    worker = QRLoginWorker(
        create_session_func=fake_create_session,
        poll_session_func=fake_poll_session,
        verify_cookie_func=fake_verify_cookie,
        load_config_func=fake_load_config,
        save_config_func=fake_save_config,
    )
    worker.status_changed.connect(state["statuses"].append)

    with qtbot.waitSignal(worker.login_success, timeout=2000) as blocker:
        worker.start()

    worker.wait(1000)

    assert blocker.args[0]["DedeUserID"] == "24680"
    assert state["verify_called"] is True
    assert state["saved"] is not None
    assert state["saved"]["uid"] == "24680"
    assert state["saved"]["cookie"] == "SESSDATA=sess-abc; DedeUserID=24680"
    assert state["saved"]["settings"] == {"max_workers_crawl": 8}
    assert any("等待扫码" in s for s in state["statuses"])
    assert any("已扫码" in s for s in state["statuses"])
    assert state["statuses"][-1] == "扫码登录成功，Cookie 已保存"
