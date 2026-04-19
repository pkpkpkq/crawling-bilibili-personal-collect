"""Dashboard stats repository module."""

from collections import OrderedDict

from . import core


def get_stats(conn):
    """Stable stats contract for dashboard consumers."""
    stats = core.get_stats(conn)
    stats["duration_distribution"] = OrderedDict(stats["duration_distribution"])
    return stats
