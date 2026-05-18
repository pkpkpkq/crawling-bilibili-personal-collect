"""FilterBar — horizontal search + optional sort combo."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLineEdit, QWidget

from app.theme import Spacing
from app.ui.strings import PLACEHOLDER_SEARCH_GENERAL


class FilterBar(QWidget):
    """Horizontal search input with an optional sort combo box.

    Exposes ``search_input`` and ``sort_combo`` attributes for
    page-level wiring.
    """

    def __init__(self, sort_items: list[str] | None = None, parent=None):
        super().__init__(parent)
        self.setObjectName("filter-bar")

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(PLACEHOLDER_SEARCH_GENERAL)
        self.search_input.setObjectName("filter-bar-search-input")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.SCALE_8)
        layout.addWidget(self.search_input, alignment=Qt.AlignmentFlag.AlignVCenter)

        self.sort_combo: QComboBox | None = None
        if sort_items is not None:
            self.sort_combo = QComboBox()
            self.sort_combo.setObjectName("filter-bar-sort-combo")
            self.sort_combo.addItems(sort_items)
            layout.addWidget(self.sort_combo, alignment=Qt.AlignmentFlag.AlignVCenter)
