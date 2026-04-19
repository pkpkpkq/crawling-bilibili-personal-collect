import json
from typing import Any, Mapping

DEFAULT_CONFIG_PATH = "config.json"

DEFAULT_SETTINGS = {
    "max_workers_crawl": 3,
    "max_workers_image": 10,
    "page_delay": 0.3,
    "image_retry": 3,
    "backup_keep_count": 5,
    "enable_incremental": True,
    "csv_export": True,
}


class ConfigServiceError(Exception):
    """Base exception for config service failures."""


class ConfigFileMissingError(ConfigServiceError):
    """Raised when config file cannot be found."""


class ConfigDecodeError(ConfigServiceError):
    """Raised when config JSON is malformed."""


class ConfigValidationError(ConfigServiceError):
    """Raised when required config fields are missing."""


def merge_settings(settings: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Merge provided settings with default values."""
    settings = settings or {}
    return {**DEFAULT_SETTINGS, **dict(settings)}


def load_config(path: str = DEFAULT_CONFIG_PATH) -> tuple[Any, str, dict[str, Any]]:
    """Load config JSON and merge settings with defaults."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
    except FileNotFoundError as exc:
        raise ConfigFileMissingError(str(exc)) from exc
    except json.JSONDecodeError as exc:
        raise ConfigDecodeError(str(exc)) from exc

    uid = config.get("uid")
    if not uid:
        raise ConfigValidationError("missing_uid")

    cookie = config.get("cookie") or ""
    settings = merge_settings(config.get("settings", {}))

    return uid, cookie, settings


def build_config(
    uid: Any,
    cookie: str,
    settings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a shape-compatible config payload."""
    return {"uid": uid, "cookie": cookie, "settings": merge_settings(settings)}


def save_config(
    uid: Any,
    cookie: str,
    path: str = DEFAULT_CONFIG_PATH,
    settings: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist config JSON using the existing shape contract."""
    config = build_config(uid=uid, cookie=cookie, settings=settings)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)
    return config
