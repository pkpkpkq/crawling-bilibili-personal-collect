"""Collection repository module with stable Python structures."""

from . import core


def _to_dict(row):
    return dict(row) if row is not None else None


def _to_dicts(rows):
    return [dict(row) for row in rows]


def upsert_collection(conn, coll_id, name, media_count, api_mtime=0):
    return core.upsert_collection(conn, coll_id, name, media_count, api_mtime)


def get_all_collections(conn):
    """Stable list-of-dicts view of collections."""
    return _to_dicts(core.get_all_collections(conn))


def get_collection_by_id(conn, coll_id):
    """Stable dict view of a single collection."""
    return _to_dict(core.get_collection_by_id(conn, coll_id))


def get_collection_media_count(conn, coll_id):
    return core.get_collection_media_count(conn, coll_id)


def get_collection_incremental_info(conn, coll_id):
    return core.get_collection_incremental_info(conn, coll_id)
