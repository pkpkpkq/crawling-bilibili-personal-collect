from __future__ import annotations

import math
from typing import Any

from PySide6.QtCore import QModelIndex, QSortFilterProxyModel, Qt

from .collection_rows_model import CollectionRowRole
from .common import (
    casefold_text,
    parse_date_boundary,
    parse_datetime,
    parse_duration_to_seconds,
    safe_int,
)
from .global_search_rows_model import GlobalSearchRowRole
from .up_list_rows_model import UpListRowRole


class CollectionFilterProxyModel(QSortFilterProxyModel):
    """Filter/sort proxy preserving legacy folder-page behavior."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_text = ""
        self._show_current_only = False
        self._fav_start = None
        self._fav_end = None
        self._pub_start = None
        self._pub_end = None
        self._sort_key = "fav_desc"

        self.setDynamicSortFilter(True)
        self.sort(0, Qt.SortOrder.AscendingOrder)

    def _role_value(self, source_row: int, role: CollectionRowRole) -> Any:
        model = self.sourceModel()
        if model is None:
            return None
        index = model.index(source_row, 0, QModelIndex())
        if not index.isValid():
            return None
        return model.data(index, int(role))

    def setSearchText(self, text: str | None) -> None:  # noqa: N802
        normalized = casefold_text(text).strip()
        if self._search_text == normalized:
            return
        self._search_text = normalized
        self.invalidate()

    def setShowCurrentOnly(self, enabled: bool) -> None:  # noqa: N802
        enabled = bool(enabled)
        if self._show_current_only == enabled:
            return
        self._show_current_only = enabled
        self.invalidate()

    def setFavoriteDateRange(self, start, end) -> None:  # noqa: N802
        parsed_start = parse_date_boundary(start)
        parsed_end = parse_date_boundary(end)
        if (self._fav_start, self._fav_end) == (parsed_start, parsed_end):
            return
        self._fav_start = parsed_start
        self._fav_end = parsed_end
        self.invalidate()

    def setPublishDateRange(self, start, end) -> None:  # noqa: N802
        parsed_start = parse_date_boundary(start)
        parsed_end = parse_date_boundary(end)
        if (self._pub_start, self._pub_end) == (parsed_start, parsed_end):
            return
        self._pub_start = parsed_start
        self._pub_end = parsed_end
        self.invalidate()

    def setSortKey(self, key: str | None) -> None:  # noqa: N802
        normalized = key or "fav_desc"
        if self._sort_key == normalized:
            return
        self._sort_key = normalized
        self.invalidate()
        self.sort(0, Qt.SortOrder.AscendingOrder)

    def sortKey(self) -> str:  # noqa: N802
        return self._sort_key

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:  # noqa: N802
        if source_parent.isValid():
            return True

        title = casefold_text(self._role_value(source_row, CollectionRowRole.TITLE))
        bv_id = casefold_text(self._role_value(source_row, CollectionRowRole.BV_ID))
        up_name = casefold_text(self._role_value(source_row, CollectionRowRole.UP_NAME))

        if (
            self._search_text
            and self._search_text not in title
            and self._search_text not in bv_id
            and self._search_text not in up_name
        ):
            return False

        if self._show_current_only and not bool(
            self._role_value(source_row, CollectionRowRole.IS_CURRENT)
        ):
            return False

        fav_dt = parse_datetime(self._role_value(source_row, CollectionRowRole.FAV_TIME))
        pub_dt = parse_datetime(self._role_value(source_row, CollectionRowRole.PUBLISH_TIME))

        if self._fav_start and (fav_dt is None or fav_dt.date() < self._fav_start):
            return False
        if self._fav_end and (fav_dt is None or fav_dt.date() > self._fav_end):
            return False
        if self._pub_start and (pub_dt is None or pub_dt.date() < self._pub_start):
            return False
        if self._pub_end and (pub_dt is None or pub_dt.date() > self._pub_end):
            return False

        return True

    @staticmethod
    def _compare(left: Any, right: Any, *, descending: bool = False) -> bool:
        left_missing = left is None
        right_missing = right is None

        # Keep malformed/missing values at the end regardless of direction.
        if left_missing and right_missing:
            return False
        if left_missing:
            return False
        if right_missing:
            return True

        if descending:
            return left > right
        return left < right

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:  # noqa: N802
        left_row = left.row()
        right_row = right.row()

        key = self._sort_key
        if key in {"fav_desc", "fav_asc"}:
            left_value = parse_datetime(self._role_value(left_row, CollectionRowRole.FAV_TIME))
            right_value = parse_datetime(self._role_value(right_row, CollectionRowRole.FAV_TIME))
            result = self._compare(left_value, right_value, descending=(key == "fav_desc"))
        elif key in {"pub_desc", "pub_asc"}:
            left_value = parse_datetime(
                self._role_value(left_row, CollectionRowRole.PUBLISH_TIME)
            )
            right_value = parse_datetime(
                self._role_value(right_row, CollectionRowRole.PUBLISH_TIME)
            )
            result = self._compare(left_value, right_value, descending=(key == "pub_desc"))
        elif key == "play_desc":
            left_value = safe_int(self._role_value(left_row, CollectionRowRole.PLAY_COUNT), 0)
            right_value = safe_int(self._role_value(right_row, CollectionRowRole.PLAY_COUNT), 0)
            result = self._compare(left_value, right_value, descending=True)
        elif key == "collect_desc":
            left_value = safe_int(
                self._role_value(left_row, CollectionRowRole.COLLECT_COUNT), 0
            )
            right_value = safe_int(
                self._role_value(right_row, CollectionRowRole.COLLECT_COUNT), 0
            )
            result = self._compare(left_value, right_value, descending=True)
        elif key == "danmaku_desc":
            left_value = safe_int(
                self._role_value(left_row, CollectionRowRole.DANMAKU_COUNT), 0
            )
            right_value = safe_int(
                self._role_value(right_row, CollectionRowRole.DANMAKU_COUNT), 0
            )
            result = self._compare(left_value, right_value, descending=True)
        elif key == "duration_desc":
            left_value = parse_duration_to_seconds(
                self._role_value(left_row, CollectionRowRole.DURATION)
            )
            right_value = parse_duration_to_seconds(
                self._role_value(right_row, CollectionRowRole.DURATION)
            )
            result = self._compare(left_value, right_value, descending=True)
        else:
            left_value = casefold_text(self._role_value(left_row, CollectionRowRole.TITLE))
            right_value = casefold_text(self._role_value(right_row, CollectionRowRole.TITLE))
            result = self._compare(left_value, right_value)

        if left_value == right_value:
            return left_row < right_row
        return result


class GlobalSearchFilterProxyModel(QSortFilterProxyModel):
    """Filter/sort proxy for global search keyword matching."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_text = ""
        self._sort_key = "fav_desc"  # default: latest fav time descending
        self.setDynamicSortFilter(True)
        self.sort(0, Qt.SortOrder.AscendingOrder)

    def _role_value(self, source_row: int, role: GlobalSearchRowRole) -> Any:
        model = self.sourceModel()
        if model is None:
            return None
        index = model.index(source_row, 0, QModelIndex())
        if not index.isValid():
            return None
        return model.data(index, int(role))

    def setSearchText(self, text: str | None) -> None:  # noqa: N802
        normalized = casefold_text(text).strip()
        if self._search_text == normalized:
            return
        self._search_text = normalized
        self.invalidate()

    def setSortByLatestFavorite(self, descending: bool = True) -> None:  # noqa: N802
        key = "fav_desc" if descending else "fav_asc"
        self.setSortKey(key)

    def setSortKey(self, key: str) -> None:  # noqa: N802
        if self._sort_key == key:
            return
        self._sort_key = key
        self.invalidate()
        self.sort(0, Qt.SortOrder.AscendingOrder)

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:  # noqa: N802
        if source_parent.isValid():
            return True

        if not self._search_text:
            return True

        title = casefold_text(self._role_value(source_row, GlobalSearchRowRole.TITLE))
        bvid = casefold_text(self._role_value(source_row, GlobalSearchRowRole.BV_ID))
        up_name = casefold_text(self._role_value(source_row, GlobalSearchRowRole.UP_NAME))

        return (
            self._search_text in title
            or self._search_text in bvid
            or self._search_text in up_name
        )

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:  # noqa: N802
        left_row = left.row()
        right_row = right.row()

        if self._sort_key in ("play_desc", "collect_desc"):
            raw_field = "play_count" if self._sort_key == "play_desc" else "collect_count"
            left_raw = self._role_value(left_row, GlobalSearchRowRole.RAW_ROW)
            right_raw = self._role_value(right_row, GlobalSearchRowRole.RAW_ROW)
            left_val = int((left_raw or {}).get(raw_field, 0) or 0)
            right_val = int((right_raw or {}).get(raw_field, 0) or 0)
            if left_val != right_val:
                return left_val > right_val
            # Fallback to title
            left_title = casefold_text(self._role_value(left_row, GlobalSearchRowRole.TITLE))
            right_title = casefold_text(self._role_value(right_row, GlobalSearchRowRole.TITLE))
            return left_title < right_title

        # Default: sort by latest fav time
        left_time = parse_datetime(
            self._role_value(left_row, GlobalSearchRowRole.LATEST_FAV_TIME)
        )
        right_time = parse_datetime(
            self._role_value(right_row, GlobalSearchRowRole.LATEST_FAV_TIME)
        )

        if left_time and right_time and left_time != right_time:
            if self._sort_key == "fav_desc":
                return left_time > right_time
            return left_time < right_time

        if left_time and not right_time:
            return True
        if right_time and not left_time:
            return False

        left_title = casefold_text(self._role_value(left_row, GlobalSearchRowRole.TITLE))
        right_title = casefold_text(self._role_value(right_row, GlobalSearchRowRole.TITLE))
        if left_title != right_title:
            return left_title < right_title
        return left_row < right_row


class UpListFilterProxyModel(QSortFilterProxyModel):
    """Simple in-memory UP-name filter."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._search_text = ""
        self.setDynamicSortFilter(True)
        self.sort(0, Qt.SortOrder.AscendingOrder)

    def _role_value(self, source_row: int, role: UpListRowRole) -> Any:
        model = self.sourceModel()
        if model is None:
            return None
        index = model.index(source_row, 0, QModelIndex())
        if not index.isValid():
            return None
        return model.data(index, int(role))

    def setSearchText(self, text: str | None) -> None:  # noqa: N802
        normalized = casefold_text(text).strip()
        if self._search_text == normalized:
            return
        self._search_text = normalized
        self.invalidate()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:  # noqa: N802
        if source_parent.isValid():
            return True
        if not self._search_text:
            return True

        up_name = casefold_text(self._role_value(source_row, UpListRowRole.NAME))
        return self._search_text in up_name

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:  # noqa: N802
        left_row = left.row()
        right_row = right.row()
        left_name = casefold_text(self._role_value(left_row, UpListRowRole.NAME))
        right_name = casefold_text(self._role_value(right_row, UpListRowRole.NAME))
        if left_name != right_name:
            return left_name < right_name
        return left_row < right_row


class PagedProxyModel(QSortFilterProxyModel):
    """Page-slicing proxy model with default 50-items-per-page behavior."""

    def __init__(self, page_size: int = 50, parent=None):
        super().__init__(parent)
        self._page_size = max(1, int(page_size))
        self._current_page = 1
        self.setDynamicSortFilter(True)

    def setPageSize(self, page_size: int) -> None:  # noqa: N802
        parsed = max(1, int(page_size))
        if parsed == self._page_size:
            return
        self._page_size = parsed
        self._ensure_valid_page()
        self.invalidate()

    def pageSize(self) -> int:  # noqa: N802
        return self._page_size

    def setCurrentPage(self, page: int) -> None:  # noqa: N802
        parsed = max(1, int(page))
        parsed = min(parsed, self.pageCount())
        if parsed == self._current_page:
            return
        self._current_page = parsed
        self.invalidate()

    def currentPage(self) -> int:  # noqa: N802
        return self._current_page

    def nextPage(self) -> None:  # noqa: N802
        self.setCurrentPage(self._current_page + 1)

    def previousPage(self) -> None:  # noqa: N802
        self.setCurrentPage(self._current_page - 1)

    def totalRowCount(self) -> int:  # noqa: N802
        model = self.sourceModel()
        if model is None:
            return 0
        return model.rowCount()

    def pageCount(self) -> int:  # noqa: N802
        total = self.totalRowCount()
        return max(1, math.ceil(total / self._page_size))

    def _ensure_valid_page(self) -> None:
        page_count = self.pageCount()
        self._current_page = min(max(1, self._current_page), page_count)

    def _slice_bounds(self) -> tuple[int, int]:
        self._ensure_valid_page()
        total = self.totalRowCount()
        start = (self._current_page - 1) * self._page_size
        end = min(total, start + self._page_size)
        return start, end

    def invalidate(self) -> None:  # noqa: N802
        self._ensure_valid_page()
        super().invalidate()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:  # noqa: N802
        if source_parent.isValid():
            return True
        start, end = self._slice_bounds()
        return start <= source_row < end
