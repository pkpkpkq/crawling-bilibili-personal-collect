from app.services import auth_service


def test_parse_manual_cookie_input_rejects_missing_required_fields():
    result = auth_service.parse_manual_cookie_input("SESSDATA=only")

    assert result["success"] is False
    assert result["missing_fields"] == ["DedeUserID"]


def test_verify_cookie_dict_rejects_not_logged_in_when_required():
    class DummyResponse:
        def json(self):
            return {"code": 0, "data": {"isLogin": False}}

    def fake_get(url, headers, timeout):
        return DummyResponse()

    result = auth_service.verify_cookie_dict(
        {"SESSDATA": "aaa", "DedeUserID": "123"},
        request_get=fake_get,
        require_login=True,
    )

    assert result.valid is False


def test_poll_qrcode_login_session_rejects_incomplete_cookie_payload():
    class DummyResponse:
        cookies = []

        def json(self):
            return {
                "data": {
                    "code": 0,
                    "url": "https://example.invalid/callback?SESSDATA=only",
                }
            }

    def fake_get(url, params, headers, timeout):
        return DummyResponse()

    time_values = iter([0, 1, 2])
    result = auth_service.poll_qrcode_login_session(
        "qrcode-key",
        request_get=fake_get,
        time_func=lambda: next(time_values),
        sleep_func=lambda _: None,
    )

    assert result["success"] is False
    assert result["status"] == "incomplete_cookie"
