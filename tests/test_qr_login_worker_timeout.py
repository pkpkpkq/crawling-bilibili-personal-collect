from app.workers.qr_login_worker import QRLoginWorker


def test_qr_login_worker_emits_timeout_failure(qtbot):
    def fake_create_session(**kwargs):
        return {
            "success": True,
            "qrcode_key": "key-timeout",
            "qrcode_url": "https://example.invalid/qr-timeout",
        }

    def fake_poll_session(qrcode_key, **kwargs):
        assert qrcode_key == "key-timeout"
        status_callback = kwargs["status_callback"]
        status_callback({"code": 86101, "remaining": 20})
        return {"success": False, "status": "timeout", "error": "超时：3分钟内未完成登录"}

    worker = QRLoginWorker(
        create_session_func=fake_create_session,
        poll_session_func=fake_poll_session,
        verify_cookie_func=lambda *_args, **_kwargs: None,
        load_config_func=lambda *_args, **_kwargs: ("", "", {}),
        save_config_func=lambda **_kwargs: {},
    )

    with qtbot.waitSignal(worker.login_failed, timeout=2000) as blocker:
        worker.start()

    worker.wait(1000)

    assert blocker.args == ["扫码超时，请重新获取二维码。"]


def test_qr_login_worker_emits_expired_failure(qtbot):
    def fake_create_session(**kwargs):
        return {
            "success": True,
            "qrcode_key": "key-expired",
            "qrcode_url": "https://example.invalid/qr-expired",
        }

    def fake_poll_session(qrcode_key, **kwargs):
        assert qrcode_key == "key-expired"
        return {"success": False, "status": "expired", "error": "二维码已过期"}

    worker = QRLoginWorker(
        create_session_func=fake_create_session,
        poll_session_func=fake_poll_session,
        verify_cookie_func=lambda *_args, **_kwargs: None,
        load_config_func=lambda *_args, **_kwargs: ("", "", {}),
        save_config_func=lambda **_kwargs: {},
    )

    with qtbot.waitSignal(worker.login_failed, timeout=2000) as blocker:
        worker.start()

    worker.wait(1000)

    assert blocker.args == ["二维码已过期，请重新获取。"]


def test_qr_login_worker_cancel_after_polling_returns_cancelled(qtbot):
    worker_holder = {"worker": None}

    def fake_create_session(**kwargs):
        return {
            "success": True,
            "qrcode_key": "key-cancel",
            "qrcode_url": "https://example.invalid/qr-cancel",
        }

    def fake_poll_session(qrcode_key, **kwargs):
        assert qrcode_key == "key-cancel"
        worker_holder["worker"].request_stop()
        return {
            "success": True,
            "status": "success",
            "cookie_dict": {"SESSDATA": "abc", "DedeUserID": "100"},
        }

    worker = QRLoginWorker(
        create_session_func=fake_create_session,
        poll_session_func=fake_poll_session,
        verify_cookie_func=lambda *_args, **_kwargs: None,
        load_config_func=lambda *_args, **_kwargs: ("", "", {}),
        save_config_func=lambda **_kwargs: {},
    )
    worker_holder["worker"] = worker

    with qtbot.waitSignal(worker.login_failed, timeout=2000) as blocker:
        worker.start()

    worker.wait(1000)

    assert blocker.args == ["扫码登录已取消"]
