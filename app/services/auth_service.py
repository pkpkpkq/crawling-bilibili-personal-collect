import json
import time
from dataclasses import dataclass
from typing import Any, Callable, Mapping

import requests

QRCODE_GENERATE_URL = "https://passport.bilibili.com/x/passport-login/web/qrcode/generate"
QRCODE_POLL_URL = "https://passport.bilibili.com/x/passport-login/web/qrcode/poll"
NAV_URL = "https://api.bilibili.com/x/web-interface/nav"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://www.bilibili.com/",
}

REQUIRED_COOKIE_FIELDS = ("SESSDATA", "DedeUserID")


@dataclass
class CookieVerificationResult:
    valid: bool
    data: dict[str, Any] | None = None
    error: str | None = None
    uname: str | None = None
    mid: Any | None = None


def serialize_cookie_dict(cookie_dict: Mapping[str, Any]) -> str:
    return "; ".join(f"{k}={v}" for k, v in cookie_dict.items())


def parse_cookie_string(cookie_input: str) -> dict[str, str]:
    cookie_dict: dict[str, str] = {}
    for item in cookie_input.replace("\n", "").split(";"):
        item = item.strip()
        if "=" in item:
            key, value = item.split("=", 1)
            cookie_dict[key.strip()] = value.strip()
    return cookie_dict


def validate_cookie_dict(
    cookie_dict: Mapping[str, Any],
    required_fields: tuple[str, ...] = REQUIRED_COOKIE_FIELDS,
) -> tuple[bool, list[str]]:
    missing = [field for field in required_fields if field not in cookie_dict]
    return len(missing) == 0, missing


def parse_manual_cookie_input(cookie_input: str) -> dict[str, Any]:
    cookie_dict = parse_cookie_string(cookie_input)
    is_valid, missing_fields = validate_cookie_dict(cookie_dict)
    return {
        "success": is_valid,
        "cookie_dict": cookie_dict,
        "missing_fields": missing_fields,
    }


def verify_cookie_headers(
    headers: Mapping[str, str],
    *,
    timeout: int = 10,
    require_login: bool = False,
    request_get: Callable[..., Any] = requests.get,
) -> CookieVerificationResult:
    try:
        response = request_get(NAV_URL, headers=dict(headers), timeout=timeout)
        data = response.json()

        if data.get("code") != 0:
            return CookieVerificationResult(valid=False, data=data)

        logged_in = bool(data.get("data", {}).get("isLogin"))
        if require_login and not logged_in:
            return CookieVerificationResult(valid=False, data=data)

        user_data = data.get("data", {})
        return CookieVerificationResult(
            valid=True,
            data=data,
            uname=user_data.get("uname"),
            mid=user_data.get("mid"),
        )
    except Exception as exc:  # pylint: disable=broad-except
        return CookieVerificationResult(valid=False, error=str(exc))


def verify_cookie_dict(
    cookie_dict: Mapping[str, Any],
    *,
    timeout: int = 10,
    require_login: bool = True,
    request_get: Callable[..., Any] = requests.get,
) -> CookieVerificationResult:
    cookie_str = serialize_cookie_dict(cookie_dict)
    headers = {**HEADERS, "Cookie": cookie_str}
    return verify_cookie_headers(
        headers,
        timeout=timeout,
        require_login=require_login,
        request_get=request_get,
    )


def create_qrcode_login_session(
    *,
    timeout: int = 10,
    headers: Mapping[str, str] | None = None,
    request_get: Callable[..., Any] = requests.get,
) -> dict[str, Any]:
    req_headers = dict(headers or HEADERS)
    try:
        resp = request_get(QRCODE_GENERATE_URL, headers=req_headers, timeout=timeout)
        data = resp.json()

        if data.get("code") != 0:
            return {
                "success": False,
                "status": "generate_failed",
                "error": data.get("message", "生成二维码失败"),
            }

        return {
            "success": True,
            "status": "ok",
            "qrcode_key": data["data"]["qrcode_key"],
            "qrcode_url": data["data"]["url"],
        }
    except requests.RequestException as exc:
        return {
            "success": False,
            "status": "network_error",
            "error": f"网络错误: {exc}",
        }
    except (KeyError, json.JSONDecodeError, ValueError, TypeError) as exc:
        return {
            "success": False,
            "status": "parse_error",
            "error": f"解析响应失败: {exc}",
        }


def _parse_refresh_url_cookies(refresh_url: str) -> dict[str, str]:
    cookies_from_url: dict[str, str] = {}
    if "?" not in refresh_url:
        return cookies_from_url

    params_str = refresh_url.split("?", 1)[1]
    for param in params_str.split("&"):
        if "=" in param:
            key, value = param.split("=", 1)
            cookies_from_url[key] = value
    return cookies_from_url


def _cookies_from_response(cookies: Any) -> dict[str, str]:
    cookies_from_header: dict[str, str] = {}
    if not cookies:
        return cookies_from_header

    for cookie in cookies:
        name = getattr(cookie, "name", None)
        value = getattr(cookie, "value", None)
        if name is not None and value is not None:
            cookies_from_header[name] = value
    return cookies_from_header


def poll_qrcode_login_session(
    qrcode_key: str,
    *,
    timeout_seconds: int = 180,
    poll_interval_seconds: int = 2,
    request_timeout: int = 10,
    headers: Mapping[str, str] | None = None,
    request_get: Callable[..., Any] = requests.get,
    time_func: Callable[[], float] = time.time,
    sleep_func: Callable[[float], None] = time.sleep,
    status_callback: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    req_headers = dict(headers or HEADERS)
    start_time = time_func()

    while time_func() - start_time < timeout_seconds:
        try:
            poll_resp = request_get(
                QRCODE_POLL_URL,
                params={"qrcode_key": qrcode_key},
                headers=req_headers,
                timeout=request_timeout,
            )
            poll_data = poll_resp.json()
        except requests.RequestException as exc:
            return {
                "success": False,
                "status": "network_error",
                "error": f"网络错误: {exc}",
            }
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            return {
                "success": False,
                "status": "parse_error",
                "error": f"解析响应失败: {exc}",
            }

        code = poll_data.get("data", {}).get("code", -1)
        remaining = max(0, int(timeout_seconds - (time_func() - start_time)))

        if status_callback is not None:
            status_callback({"code": code, "remaining": remaining})

        if code == 0:
            refresh_url = poll_data.get("data", {}).get("url", "")
            cookies_from_url = _parse_refresh_url_cookies(refresh_url)
            cookies_from_header = _cookies_from_response(poll_resp.cookies)
            all_cookies = {**cookies_from_url, **cookies_from_header}

            valid, missing = validate_cookie_dict(all_cookies)
            if not valid:
                return {
                    "success": False,
                    "status": "incomplete_cookie",
                    "error": "Cookie不完整，缺少必要字段",
                    "cookie_dict": all_cookies,
                    "missing_fields": missing,
                }

            return {"success": True, "status": "success", "cookie_dict": all_cookies}

        if code == 86038:
            return {"success": False, "status": "expired", "error": "二维码已过期"}

        sleep_func(poll_interval_seconds)

    return {"success": False, "status": "timeout", "error": "超时：3分钟内未完成登录"}
