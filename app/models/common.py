from __future__ import annotations

from datetime import date, datetime
from typing import Any

_DATETIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d",
)

_DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d")


def casefold_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).casefold()


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y", "on"}:
            return True
        if lowered in {"0", "false", "no", "n", "off", ""}:
            return False
    return bool(value)


def parse_duration_to_seconds(value: Any) -> int:
    if value is None:
        return 0
    if isinstance(value, (int, float)):
        return int(value)

    text = str(value).strip()
    if not text:
        return 0

    parts = text.split(":")
    try:
        numbers = [int(part) for part in parts]
    except ValueError:
        return 0

    if len(numbers) == 3:
        hours, minutes, seconds = numbers
        return hours * 3600 + minutes * 60 + seconds
    if len(numbers) == 2:
        minutes, seconds = numbers
        return minutes * 60 + seconds
    if len(numbers) == 1:
        return numbers[0]
    return 0


def parse_datetime(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day)

    text = str(value).strip()
    if not text:
        return None

    for fmt in _DATETIME_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue

    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def parse_date_boundary(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text:
        return None

    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue

    parsed = parse_datetime(text)
    return parsed.date() if parsed else None
