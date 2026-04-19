"""Compatibility shim for legacy database imports.

Concrete repository modules live under ``app.repositories`` while this module
re-exports the legacy function surface.
"""

from app.repositories.core import (
    DB_NAME,
    add_video_to_collection,
    get_all_collections,
    get_all_cover_urls,
    get_all_following_ups,
    get_all_up_face_urls,
    get_all_videos_index,
    get_collection_by_id,
    get_collection_incremental_info,
    get_collection_media_count,
    get_connection,
    get_db_path,
    get_stats,
    get_video_history,
    get_videos_in_collection,
    init_db,
    mark_unfavorited,
    migrate_from_json,
    record_crawl,
    save_collection_videos,
    save_following_ups,
    upsert_collection,
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
