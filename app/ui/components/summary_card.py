"""SummaryCard — compact metric card with title and value."""

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.theme import Spacing


class SummaryCard(QWidget):
    """Compact metric display with a small title and a large value.

    Styled via ``QLabel#summary-card-title`` and
    ``QLabel#summary-card-value`` in the base stylesheet.
    """

    def __init__(self, title: str = "", value: str = "", parent=None):
        super().__init__(parent)

        self._title_label = QLabel(title)
        self._title_label.setObjectName("summary-card-title")
        font = self._title_label.font()
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self._title_label.setFont(font)

        self._value_label = QLabel(value)
        self._value_label.setObjectName("summary-card-value")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.SCALE_4)
        layout.addWidget(self._title_label)
        layout.addWidget(self._value_label)

    @property
    def title_label(self) -> QLabel:
        return self._title_label

    @property
    def value_label(self) -> QLabel:
        return self._value_label

    def set_title(self, text: str) -> None:
        self._title_label.setText(text)

    def set_value(self, text: str) -> None:
        self._value_label.setText(text)
