"""Legacy JSON migration helpers."""

from . import core


def migrate_from_json(json_dir, db_path=None):
    return core.migrate_from_json(json_dir, db_path)
