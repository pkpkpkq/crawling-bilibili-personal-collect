import json

import pytest

from app.services import config_service


def test_merge_settings_preserves_defaults_and_overrides_known_keys():
    merged = config_service.merge_settings({"max_workers_crawl": 8, "custom": "value"})

    assert merged["max_workers_crawl"] == 8
    assert merged["max_workers_image"] == config_service.DEFAULT_SETTINGS["max_workers_image"]
    assert merged["custom"] == "value"


def test_load_config_merges_defaults(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "uid": "12345",
                "cookie": "SESSDATA=abc; DedeUserID=12345",
                "settings": {"page_delay": 1.0},
            }
        ),
        encoding="utf-8",
    )

    uid, cookie, settings = config_service.load_config(str(config_path))

    assert uid == "12345"
    assert cookie == "SESSDATA=abc; DedeUserID=12345"
    assert settings["page_delay"] == 1.0
    assert settings["image_retry"] == config_service.DEFAULT_SETTINGS["image_retry"]


def test_load_config_raises_when_missing_uid(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"cookie": "SESSDATA=abc", "settings": {}}),
        encoding="utf-8",
    )

    with pytest.raises(config_service.ConfigValidationError):
        config_service.load_config(str(config_path))


def test_save_config_persists_shape_with_default_settings(tmp_path):
    config_path = tmp_path / "config.json"

    saved = config_service.save_config(
        uid="10086",
        cookie="SESSDATA=abc; DedeUserID=10086",
        path=str(config_path),
    )

    raw = json.loads(config_path.read_text(encoding="utf-8"))
    assert raw == saved
    assert raw["uid"] == "10086"
    assert raw["cookie"] == "SESSDATA=abc; DedeUserID=10086"
    assert raw["settings"] == config_service.DEFAULT_SETTINGS
