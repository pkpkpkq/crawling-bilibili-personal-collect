"""PaginationBar — prev / page-indicator / next navigation bar."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from app.theme import Spacing
from app.ui.strings import BTN_NEXT_PAGE, BTN_PREV_PAGE, PAGINATION_FORMAT


class PaginationBar(QWidget):
    """Horizontal prev / page-label / next navigation bar.

    Both buttons start **disabled**.  Call ``update(current, total_pages,
    total_items)`` to enable/disable them and refresh the page label.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("pagination-bar")

        self._prev_btn = QPushButton(BTN_PREV_PAGE)
        self._prev_btn.setEnabled(False)
        self._prev_btn.setFixedWidth(80)
        self._prev_btn.setObjectName("pagination-prev-btn")

        self._page_label = QLabel("")
        self._page_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._page_label.setObjectName("pagination-page-label")

        self._next_btn = QPushButton(BTN_NEXT_PAGE)
        self._next_btn.setEnabled(False)
        self._next_btn.setFixedWidth(80)
        self._next_btn.setObjectName("pagination-next-btn")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.SCALE_8)
        layout.addWidget(self._prev_btn, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch()
        layout.addWidget(self._page_label, alignment=Qt.AlignmentFlag.AlignVCenter)
        layout.addStretch()
        layout.addWidget(self._next_btn, alignment=Qt.AlignmentFlag.AlignVCenter)

    @property
    def prev_button(self) -> QPushButton:
        return self._prev_btn

    @property
    def next_button(self) -> QPushButton:
        return self._next_btn

    @property
    def page_label(self) -> QLabel:
        return self._page_label

    def update(self, current: int, total_pages: int, total_items: int) -> None:
        self._page_label.setText(
            PAGINATION_FORMAT.format(
                current=current,
                total_pages=total_pages,
                total_items=total_items,
            )
        )
        self._prev_btn.setEnabled(current > 1)
        self._next_btn.setEnabled(current < total_pages)
