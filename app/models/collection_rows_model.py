from __future__ import annotations

from enum import IntEnum
from typing import Any, Iterable

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from .common import normalize_bool, safe_int


class CollectionRowRole(IntEnum):
    RAW_ROW = int(Qt.ItemDataRole.UserRole) + 1
    TITLE = RAW_ROW + 1
    BV_ID = RAW_ROW + 2
    UP_NAME = RAW_ROW + 3
    FAV_TIME = RAW_ROW + 4
    PUBLISH_TIME = RAW_ROW + 5
    PLAY_COUNT = RAW_ROW + 6
    COLLECT_COUNT = RAW_ROW + 7
    DANMAKU_COUNT = RAW_ROW + 8
    DURATION = RAW_ROW + 9
    IS_INVALID = RAW_ROW + 10
    IS_ACTIVE = RAW_ROW + 11
    IS_CURRENT = RAW_ROW + 12
    COLLECTION_NAME = RAW_ROW + 13
    LATEST_COLLECTION = RAW_ROW + 14
    HISTORY = RAW_ROW + 15


class CollectionRowsModel(QAbstractTableModel):
    COLUMNS = (
        ("title", "标题"),
        ("bv_id", "BV号"),
        ("up_name", "UP主"),
        ("fav_time", "收藏时间"),
        ("publish_time", "发布时间"),
        ("play_count", "播放量"),
        ("collect_count", "收藏量"),
        ("danmaku_count", "弹幕数"),
        ("duration", "时长"),
    )

    _ROLE_NAMES = {
        CollectionRowRole.RAW_ROW: b"raw_row",
        CollectionRowRole.TITLE: b"title",
        CollectionRowRole.BV_ID: b"bv_id",
        CollectionRowRole.UP_NAME: b"up_name",
        CollectionRowRole.FAV_TIME: b"fav_time",
        CollectionRowRole.PUBLISH_TIME: b"publish_time",
        CollectionRowRole.PLAY_COUNT: b"play_count",
        CollectionRowRole.COLLECT_COUNT: b"collect_count",
        CollectionRowRole.DANMAKU_COUNT: b"danmaku_count",
        CollectionRowRole.DURATION: b"duration",
        CollectionRowRole.IS_INVALID: b"is_invalid",
        CollectionRowRole.IS_ACTIVE: b"is_active",
        CollectionRowRole.IS_CURRENT: b"is_current",
        CollectionRowRole.COLLECTION_NAME: b"collection_name",
        CollectionRowRole.LATEST_COLLECTION: b"latest_collection",
        CollectionRowRole.HISTORY: b"history",
    }

    def __init__(self, rows: Iterable[dict[str, Any]] | None = None, parent=None):
        super().__init__(parent)
        self._rows: list[dict[str, Any]] = []
        self.set_rows(rows or [])

    def set_rows(self, rows: Iterable[dict[str, Any]]) -> None:
        self.beginResetModel()
        self._rows = [dict(row) for row in rows]
        self.endResetModel()

    def rows(self) -> list[dict[str, Any]]:
        return list(self._rows)

    def row_dict(self, row: int) -> dict[str, Any]:
        return self._rows[row]

    @staticmethod
    def _is_current(row: dict[str, Any]) -> bool:
        is_invalid = normalize_bool(row.get("is_invalid"))
        is_active = normalize_bool(row.get("is_active", True))
        collection_name = row.get("collection_name")
        latest_collection = row.get("latest_collection")

        moved = not is_active
        if latest_collection and collection_name:
            moved = latest_collection != collection_name

        return (not is_invalid) and (not moved)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self.COLUMNS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal and 0 <= section < len(self.COLUMNS):
            return self.COLUMNS[section][1]
        return super().headerData(section, orientation, role)

    def roleNames(self):  # noqa: N802
        role_names = super().roleNames()
        for role, name in self._ROLE_NAMES.items():
            role_names[int(role)] = name
        return role_names

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):  # noqa: N802
        if not index.isValid() or not (0 <= index.row() < len(self._rows)):
            return None

        row = self._rows[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            key = self.COLUMNS[index.column()][0]
            return row.get(key)

        if role == int(CollectionRowRole.RAW_ROW):
            return row
        if role == int(CollectionRowRole.TITLE):
            return row.get("title", "")
        if role == int(CollectionRowRole.BV_ID):
            return row.get("bv_id", "")
        if role == int(CollectionRowRole.UP_NAME):
            return row.get("up_name", "")
        if role == int(CollectionRowRole.FAV_TIME):
            return row.get("fav_time")
        if role == int(CollectionRowRole.PUBLISH_TIME):
            return row.get("publish_time")
        if role == int(CollectionRowRole.PLAY_COUNT):
            return safe_int(row.get("play_count"), 0)
        if role == int(CollectionRowRole.COLLECT_COUNT):
            return safe_int(row.get("collect_count"), 0)
        if role == int(CollectionRowRole.DANMAKU_COUNT):
            return safe_int(row.get("danmaku_count"), 0)
        if role == int(CollectionRowRole.DURATION):
            return row.get("duration", "")
        if role == int(CollectionRowRole.IS_INVALID):
            return normalize_bool(row.get("is_invalid"))
        if role == int(CollectionRowRole.IS_ACTIVE):
            return normalize_bool(row.get("is_active", True))
        if role == int(CollectionRowRole.IS_CURRENT):
            return self._is_current(row)
        if role == int(CollectionRowRole.COLLECTION_NAME):
            return row.get("collection_name", "")
        if role == int(CollectionRowRole.LATEST_COLLECTION):
            return row.get("latest_collection")
        if role == int(CollectionRowRole.HISTORY):
            history = row.get("history")
            return history if isinstance(history, list) else []

        return None
