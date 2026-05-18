"""SummaryCard — compact metric card with title and value in a surface container."""

from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from app.theme import BorderRadius, Color, Spacing, Typography


class SummaryCard(QWidget):
    """Compact metric display with a small title and a large value.

    Renders as an elevated card with ivory background, warm border,
    and a subtle shadow — matching the warm editorial design system.
    """

    def __init__(self, title: str = "", value: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("summary-card-container")
        self.setStyleSheet(f"""
            QWidget#summary-card-container {{
                background-color: {Color.PURE_WHITE.value};
                border: 1px solid {Color.RING_WARM.value};
                border-radius: {BorderRadius.ROUNDED}px;
            }}
        """)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow_color = QColor(Color.ANTHROPIC_NEAR_BLACK.value)
        shadow_color.setAlpha(10)
        shadow.setColor(shadow_color)
        shadow.setOffset(0, 2)
        self.setGraphicsEffect(shadow)

        self._title_label = QLabel(title)
        self._title_label.setObjectName("summary-card-title")
        font = self._title_label.font()
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self._title_label.setFont(font)

        self._value_label = QLabel(value)
        self._value_label.setObjectName("summary-card-value")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            Spacing.SCALE_16,
            Spacing.SCALE_12,
            Spacing.SCALE_16,
            Spacing.SCALE_12,
        )
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
