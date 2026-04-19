import main


def test_main_load_config_delegates_and_keeps_cookie_warning_behavior(monkeypatch):
    monkeypatch.setattr(
        main,
        "load_config_service",
        lambda: ("uid-1", "", {"max_workers_crawl": 9, "backup_keep_count": 5}),
    )

    warnings = []
    monkeypatch.setattr(main.logging, "warning", lambda msg: warnings.append(msg))

    uid, cookie, settings = main.load_config()

    assert uid == "uid-1"
    assert cookie == ""
    assert settings["max_workers_crawl"] == 9
    assert any("缺少 'cookie'" in msg for msg in warnings)


def test_main_verify_cookie_delegates_to_auth_service(monkeypatch):
    called = {}

    def fake_verify(headers, timeout, require_login):
        called["headers"] = headers
        called["timeout"] = timeout
        called["require_login"] = require_login
        return type("Result", (), {"valid": True, "error": None})()

    monkeypatch.setattr(main, "verify_cookie_headers", fake_verify)

    ok = main.verify_cookie({"cookie": "x"})

    assert ok is True
    assert called["headers"] == {"cookie": "x"}
    assert called["timeout"] == 5
    assert called["require_login"] is False
