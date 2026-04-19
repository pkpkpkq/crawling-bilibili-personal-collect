import json

import getcookie
import main
from app.services.config_service import DEFAULT_SETTINGS


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


def test_getcookie_save_config_delegates_to_config_service(tmp_path, monkeypatch):
    target = tmp_path / "config.json"

    def fake_save(uid, cookie):
        payload = {
            "uid": uid,
            "cookie": cookie,
            "settings": dict(DEFAULT_SETTINGS),
        }
        target.write_text(json.dumps(payload), encoding="utf-8")
        return payload

    monkeypatch.setattr(getcookie, "save_config_service", fake_save)

    ok = getcookie.save_config({"SESSDATA": "aaa", "DedeUserID": "123"})

    assert ok is True
    raw = json.loads(target.read_text(encoding="utf-8"))
    assert raw["uid"] == "123"
    assert raw["cookie"] == "SESSDATA=aaa; DedeUserID=123"
    assert raw["settings"]["enable_incremental"] is True


def test_getcookie_verify_cookie_delegates_to_auth_service(monkeypatch):
    class Result:
        valid = True
        uname = "tester"
        mid = "123"
        error = None

    captured = {}

    def fake_verify(cookie_dict, timeout, require_login):
        captured["cookie_dict"] = cookie_dict
        captured["timeout"] = timeout
        captured["require_login"] = require_login
        return Result()

    monkeypatch.setattr(getcookie, "verify_cookie_dict", fake_verify)

    assert getcookie.verify_cookie({"SESSDATA": "aaa", "DedeUserID": "123"}) is True
    assert captured["cookie_dict"]["SESSDATA"] == "aaa"
    assert captured["timeout"] == 10
    assert captured["require_login"] is True


def test_getcookie_manual_input_parses_through_service(monkeypatch):
    inputs = iter(["SESSDATA=aaa; DedeUserID=123"])
    monkeypatch.setattr("builtins.input", lambda: next(inputs))

    monkeypatch.setattr(
        getcookie,
        "parse_manual_cookie_input",
        lambda value: {
            "success": True,
            "cookie_dict": {"SESSDATA": "aaa", "DedeUserID": "123"},
            "missing_fields": [],
        },
    )

    result = getcookie.manual_input()
    assert result == {"SESSDATA": "aaa", "DedeUserID": "123"}



def test_getcookie_qrcode_login_delegates_to_auth_service(monkeypatch):
    monkeypatch.setattr(
        getcookie,
        "create_qrcode_login_session",
        lambda: {
            "success": True,
            "qrcode_key": "k-1",
            "qrcode_url": "https://example.invalid/qr",
        },
    )

    captured = {}

    def fake_poll(qrcode_key, **kwargs):
        captured["qrcode_key"] = qrcode_key
        assert "status_callback" in kwargs
        return {
            "success": True,
            "status": "success",
            "cookie_dict": {"SESSDATA": "aaa", "DedeUserID": "123"},
        }

    monkeypatch.setattr(getcookie, "poll_qrcode_login_session", fake_poll)
    monkeypatch.setattr(getcookie, "print_qrcode_ascii", lambda url: True)

    result = getcookie.qrcode_login()

    assert captured["qrcode_key"] == "k-1"
    assert result == {"SESSDATA": "aaa", "DedeUserID": "123"}
