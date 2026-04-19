"""Following-UP repository module with stable Python structures."""

from . import core


def save_following_ups(conn, ups_list):
    return core.save_following_ups(conn, ups_list)


def get_all_following_ups(conn):
    """Stable list-of-dicts followed-UP source."""
    return [dict(row) for row in core.get_all_following_ups(conn)]
