from __future__ import annotations

from enum import IntEnum
from typing import Any, Iterable, Mapping

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from .common import normalize_bool


class GlobalSearchRowRole(IntEnum):
    RAW_ROW = int(Qt.ItemDataRole.UserRole) + 101
    TITLE = RAW_ROW + 1
    BV_ID = RAW_ROW + 2
    UP_NAME = RAW_ROW + 3
    UP_ID = RAW_ROW + 4
    LATEST_COLLECTION = RAW_ROW + 5
    LATEST_FAV_TIME = RAW_ROW + 6
    IS_INVALID = RAW_ROW + 7
    IS_UNFAVORITED = RAW_ROW + 8
    HISTORY = RAW_ROW + 9
    COVER_PATH = RAW_ROW + 10
    UP_FACE_PATH = RAW_ROW + 11


class GlobalSearchRowsModel(QAbstractTableModel):
    COLUMNS = (
        ("title", "标题"),
        ("bvid", "BV号"),
        ("up_name", "UP主"),
        ("latest_collection", "最新所在收藏夹"),
        ("latest_fav_time", "最新收藏时间"),
    )

    _ROLE_NAMES = {
        GlobalSearchRowRole.RAW_ROW: b"raw_row",
        GlobalSearchRowRole.TITLE: b"title",
        GlobalSearchRowRole.BV_ID: b"bvid",
        GlobalSearchRowRole.UP_NAME: b"up_name",
        GlobalSearchRowRole.UP_ID: b"up_id",
        GlobalSearchRowRole.LATEST_COLLECTION: b"latest_collection",
        GlobalSearchRowRole.LATEST_FAV_TIME: b"latest_fav_time",
        GlobalSearchRowRole.IS_INVALID: b"is_invalid",
        GlobalSearchRowRole.IS_UNFAVORITED: b"is_unfavorited",
        GlobalSearchRowRole.HISTORY: b"history",
        GlobalSearchRowRole.COVER_PATH: b"cover_path",
        GlobalSearchRowRole.UP_FACE_PATH: b"up_face_path",
    }

    def __init__(
        self,
        rows: Mapping[str, dict[str, Any]] | Iterable[dict[str, Any]] | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self._rows: list[dict[str, Any]] = []
        self.set_rows(rows or [])

    @staticmethod
    def _normalize_row(raw_row: dict[str, Any]) -> dict[str, Any]:
        info = raw_row.get("info") if isinstance(raw_row.get("info"), dict) else {}
        history = raw_row.get("history")

        return {
            "bvid": raw_row.get("bvid") or raw_row.get("bv_id") or "",
            "title": info.get("title", ""),
            "up_name": info.get("up_name", ""),
            "up_id": info.get("up_id"),
            "is_invalid": normalize_bool(info.get("is_invalid")),
            "is_unfavorited": normalize_bool(info.get("is_unfavorited")),
            "cover_path": info.get("cover_path", ""),
            "up_face_path": info.get("up_face_path", ""),
            "history": history if isinstance(history, list) else [],
            "latest_collection": raw_row.get("latest_collection", "N/A"),
            "latest_fav_time": raw_row.get("latest_fav_time", "N/A"),
        }

    @classmethod
    def _normalize_rows(
        cls, rows: Mapping[str, dict[str, Any]] | Iterable[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        iterable: Iterable[dict[str, Any]]
        if isinstance(rows, Mapping):
            iterable = rows.values()
        else:
            iterable = rows

        normalized = []
        for row in iterable:
            if isinstance(row, dict):
                normalized.append(cls._normalize_row(row))
        return normalized

    def set_rows(self, rows: Mapping[str, dict[str, Any]] | Iterable[dict[str, Any]]) -> None:
        self.beginResetModel()
        self._rows = self._normalize_rows(rows)
        self.endResetModel()

    def rows(self) -> list[dict[str, Any]]:
        return list(self._rows)

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

        if role == int(GlobalSearchRowRole.RAW_ROW):
            return row
        if role == int(GlobalSearchRowRole.TITLE):
            return row.get("title", "")
        if role == int(GlobalSearchRowRole.BV_ID):
            return row.get("bvid", "")
        if role == int(GlobalSearchRowRole.UP_NAME):
            return row.get("up_name", "")
        if role == int(GlobalSearchRowRole.UP_ID):
            return row.get("up_id")
        if role == int(GlobalSearchRowRole.LATEST_COLLECTION):
            return row.get("latest_collection", "N/A")
        if role == int(GlobalSearchRowRole.LATEST_FAV_TIME):
            return row.get("latest_fav_time", "N/A")
        if role == int(GlobalSearchRowRole.IS_INVALID):
            return normalize_bool(row.get("is_invalid"))
        if role == int(GlobalSearchRowRole.IS_UNFAVORITED):
            return normalize_bool(row.get("is_unfavorited"))
        if role == int(GlobalSearchRowRole.HISTORY):
            history = row.get("history")
            return history if isinstance(history, list) else []
        if role == int(GlobalSearchRowRole.COVER_PATH):
            return row.get("cover_path", "")
        if role == int(GlobalSearchRowRole.UP_FACE_PATH):
            return row.get("up_face_path", "")

        return None
