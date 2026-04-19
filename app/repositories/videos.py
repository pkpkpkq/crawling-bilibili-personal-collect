"""Video repository module with stable Python structures."""

from . import core


def _to_dicts(rows):
    return [dict(row) for row in rows]


def upsert_up(conn, mid, name, face_url):
    return core.upsert_up(conn, mid, name, face_url)


def upsert_video(conn, video_data):
    return core.upsert_video(conn, video_data)


def add_video_to_collection(conn, bv_id, collection_id, fav_time):
    return core.add_video_to_collection(conn, bv_id, collection_id, fav_time)


def mark_unfavorited(conn, bv_id, collection_id):
    return core.mark_unfavorited(conn, bv_id, collection_id)


def save_collection_videos(conn, collection_id, collection_name, processed_videos):
    return core.save_collection_videos(conn, collection_id, collection_name, processed_videos)


def get_videos_in_collection(conn, collection_id, include_unfav=True):
    """Stable list-of-dicts collection-detail dataset."""
    return _to_dicts(core.get_videos_in_collection(conn, collection_id, include_unfav))


def get_all_videos_index(conn):
    """Stable global search index source structure."""
    return core.get_all_videos_index(conn)


def get_all_up_face_urls(conn):
    return core.get_all_up_face_urls(conn)


def get_all_cover_urls(conn):
    return core.get_all_cover_urls(conn)
