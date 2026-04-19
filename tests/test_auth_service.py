from types import SimpleNamespace

from app.services import auth_service


class DummyResponse:
    def __init__(self, payload, cookies=None):
        self._payload = payload
        self.cookies = cookies or []

    def json(self):
        return self._payload


def test_serialize_cookie_dict_uses_semicolon_separator():
    cookie_str = auth_service.serialize_cookie_dict({"SESSDATA": "aaa", "DedeUserID": "123"})
    assert cookie_str == "SESSDATA=aaa; DedeUserID=123"


def test_parse_manual_cookie_input_parses_and_validates_required_keys():
    result = auth_service.parse_manual_cookie_input(
        "SESSDATA=aaa; DedeUserID=123; bili_jct=bbb"
    )
    assert result["success"] is True
    assert result["cookie_dict"]["SESSDATA"] == "aaa"
    assert result["cookie_dict"]["DedeUserID"] == "123"


def test_verify_cookie_dict_returns_user_info_when_logged_in():
    def fake_get(url, headers, timeout):
        assert url == auth_service.NAV_URL
        assert "Cookie" in headers
        return DummyResponse({"code": 0, "data": {"isLogin": True, "uname": "tester", "mid": 42}})

    result = auth_service.verify_cookie_dict(
        {"SESSDATA": "aaa", "DedeUserID": "42"},
        request_get=fake_get,
    )

    assert result.valid is True
    assert result.uname == "tester"
    assert result.mid == 42


def test_create_qrcode_login_session_returns_key_and_url():
    def fake_get(url, headers, timeout):
        assert url == auth_service.QRCODE_GENERATE_URL
        return DummyResponse(
            {
                "code": 0,
                "data": {"qrcode_key": "k123", "url": "https://example.invalid/qr"},
            }
        )

    result = auth_service.create_qrcode_login_session(request_get=fake_get)

    assert result["success"] is True
    assert result["qrcode_key"] == "k123"
    assert result["qrcode_url"] == "https://example.invalid/qr"


def test_poll_qrcode_login_session_merges_url_and_response_cookies():
    cookies = [
        SimpleNamespace(name="SESSDATA", value="from_header"),
        SimpleNamespace(name="DedeUserID", value="1000"),
    ]

    def fake_get(url, params, headers, timeout):
        assert url == auth_service.QRCODE_POLL_URL
        return DummyResponse(
            {
                "data": {
                    "code": 0,
                    "url": "https://example.invalid/callback?SESSDATA=from_url&DedeUserID=999",
                }
            },
            cookies=cookies,
        )

    time_values = iter([0, 1, 2])
    result = auth_service.poll_qrcode_login_session(
        "qrcode-key",
        request_get=fake_get,
        time_func=lambda: next(time_values),
        sleep_func=lambda _: None,
    )

    assert result["success"] is True
    assert result["cookie_dict"]["SESSDATA"] == "from_header"
    assert result["cookie_dict"]["DedeUserID"] == "1000"
