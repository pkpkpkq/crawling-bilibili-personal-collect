"""StatusBadge — coloured inline badge with kind-based colour switching."""

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel

from app.theme import Color


class StatusBadge(QLabel):
    """Inline status badge that switches colour by kind.

    Supported kinds: ``"info"``, ``"success"``, ``"error"``.
    Styled via ``QLabel#status-badge`` in the base stylesheet;
    per-kind colour overrides are applied through a local
    stylesheet on the same selector.
    """

    _KIND_COLORS = {
        "info": Color.CHARCOAL_WARM,
        "success": Color.TERRACOTTA_BRAND,
        "error": Color.ERROR_CRIMSON,
    }

    def __init__(self, text: str = "", kind: str = "info", parent=None):
        super().__init__(text, parent)
        self.setObjectName("status-badge")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.font()
        font.setLetterSpacing(QFont.SpacingType.AbsoluteSpacing, 1)
        self.setFont(font)
        self.set_status(text, kind)

    def set_status(self, text: str, kind: str = "info") -> None:
        self.setText(text)
        color = self._KIND_COLORS.get(kind, Color.CHARCOAL_WARM)
        self.setStyleSheet(
            f"QLabel#status-badge {{ color: {color.value}; }}"
        )
