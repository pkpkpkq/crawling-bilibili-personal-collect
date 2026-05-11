"""SurfaceCard — elevated container with ivory background."""

from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QVBoxLayout, QWidget

from app.theme import Spacing


class SurfaceCard(QWidget):
    """Card-style container with themed background and border.

    Styled via ``QWidget#surface-card`` in the base stylesheet.
    Children are added to the internal QVBoxLayout whose margins
    come from ``Spacing.CARD_PADDING``.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("surface-card")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
            Spacing.CARD_PADDING,
        )
        self._layout.setSpacing(Spacing.SCALE_12)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 13))
        shadow.setOffset(0, 3)
        self.setGraphicsEffect(shadow)

    @property
    def card_layout(self) -> QVBoxLayout:
        return self._layout
