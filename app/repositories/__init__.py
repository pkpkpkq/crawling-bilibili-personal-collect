"""Repository package exports."""

from .collections import (
    get_all_collections,
    get_collection_by_id,
    get_collection_incremental_info,
    get_collection_media_count,
    upsert_collection,
)
from .connection import DB_NAME, get_connection, get_db_path, init_db
from .following import get_all_following_ups, save_following_ups
from .history import get_video_history, record_crawl
from .migrations import migrate_from_json
from .stats import get_stats
from .videos import (
    add_video_to_collection,
    get_all_cover_urls,
    get_all_up_face_urls,
    get_all_videos_index,
    get_videos_in_collection,
    mark_unfavorited,
    save_collection_videos,
    upsert_up,
    upsert_video,
)

__all__ = [
    "DB_NAME",
    "add_video_to_collection",
    "get_all_collections",
    "get_all_cover_urls",
    "get_all_following_ups",
    "get_all_up_face_urls",
    "get_all_videos_index",
    "get_collection_by_id",
    "get_collection_incremental_info",
    "get_collection_media_count",
    "get_connection",
    "get_db_path",
    "get_stats",
    "get_video_history",
    "get_videos_in_collection",
    "init_db",
    "mark_unfavorited",
    "migrate_from_json",
    "record_crawl",
    "save_collection_videos",
    "save_following_ups",
    "upsert_collection",
    "upsert_up",
    "upsert_video",
]
