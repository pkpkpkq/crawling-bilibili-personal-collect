from __future__ import annotations

from enum import IntEnum
from typing import Any, Iterable

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt


class UpListRowRole(IntEnum):
    RAW_ROW = int(Qt.ItemDataRole.UserRole) + 201
    MID = RAW_ROW + 1
    NAME = RAW_ROW + 2
    FACE_URL = RAW_ROW + 3


class UpListRowsModel(QAbstractListModel):
    _ROLE_NAMES = {
        UpListRowRole.RAW_ROW: b"raw_row",
        UpListRowRole.MID: b"mid",
        UpListRowRole.NAME: b"name",
        UpListRowRole.FACE_URL: b"face_url",
    }

    def __init__(self, rows: Iterable[dict[str, Any]] | None = None, parent=None):
        super().__init__(parent)
        self._rows: list[dict[str, Any]] = []
        self.set_rows(rows or [])

    def set_rows(self, rows: Iterable[dict[str, Any]]) -> None:
        self.beginResetModel()
        self._rows = [dict(row) for row in rows if isinstance(row, dict)]
        self.endResetModel()

    def rows(self) -> list[dict[str, Any]]:
        return list(self._rows)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._rows)

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
            return row.get("name", "")
        if role == int(UpListRowRole.RAW_ROW):
            return row
        if role == int(UpListRowRole.MID):
            return row.get("mid")
        if role == int(UpListRowRole.NAME):
            return row.get("name", "")
        if role == int(UpListRowRole.FACE_URL):
            return row.get("face_url", "")

        return None
