"""Utilities for detecting locally downloaded videos."""

import os
import subprocess
from pathlib import Path


def find_downloaded_video(bv_id: str, download_dirs: list[str] | None = None) -> str | None:
    """Return the full path of a downloaded video matching *bv_id*, or None.

    Searches the given *download_dirs* (defaults to ``["downloads"]``) for any
    file whose name contains the BV ID.
    """
    if not bv_id:
        return None
    if download_dirs is None:
        download_dirs = ["downloads"]
    for base_dir in download_dirs:
        if not os.path.isdir(base_dir):
            continue
        # Search the base dir and one level of subdirectories (collection folders)
        for root, _dirs, files in os.walk(base_dir):
            for fname in files:
                if bv_id in fname:
                    return os.path.join(root, fname)
    return None


def open_local_video(path: str) -> None:
    """Open a video file with the system default player."""
    if os.path.isfile(path):
        os.startfile(path)


def delete_local_video(path: str) -> bool:
    """Delete a local video file. Returns True if successfully deleted."""
    try:
        if os.path.isfile(path):
            os.remove(path)
            return True
    except OSError:
        pass
    return False
