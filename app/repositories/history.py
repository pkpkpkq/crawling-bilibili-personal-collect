"""History repository module with stable Python structures."""

from . import core


def record_crawl(
    conn,
    duration_seconds,
    total_videos,
    new_videos,
    invalid_videos,
    unfav_videos,
    status="success",
):
    return core.record_crawl(
        conn,
        duration_seconds,
        total_videos,
        new_videos,
        invalid_videos,
        unfav_videos,
        status,
    )


def get_video_history(conn, bv_id):
    """Stable add/remove history contract."""
    return core.get_video_history(conn, bv_id)
