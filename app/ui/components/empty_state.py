"""EmptyState — centred placeholder when no data exists."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.theme import Spacing
from app.ui.strings import EMPTY_NO_DATA


class EmptyState(QWidget):
    """Centred empty-state placeholder with title and subtitle.

    Styled via ``QLabel#empty-state-title`` and
    ``QLabel#empty-state-subtitle`` in the base stylesheet.
    """

    def __init__(self, title: str = "", subtitle: str = "", parent=None):
        super().__init__(parent)

        if not title:
            title = EMPTY_NO_DATA

        self._title_label = QLabel(title)
        self._title_label.setObjectName("empty-state-title")
        self._title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.SCALE_4)
        layout.addStretch()
        layout.addWidget(self._title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self._subtitle_label: QLabel | None = None
        if subtitle:
            self._subtitle_label = QLabel(subtitle)
            self._subtitle_label.setObjectName("empty-state-subtitle")
            self._subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(self._subtitle_label, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

    @property
    def title_label(self) -> QLabel:
        return self._title_label

    @property
    def subtitle_label(self) -> QLabel | None:
        return self._subtitle_label

    def set_title(self, text: str) -> None:
        self._title_label.setText(text)

    def set_subtitle(self, text: str) -> None:
        if self._subtitle_label is None:
            self._subtitle_label = QLabel(text)
            self._subtitle_label.setObjectName("empty-state-subtitle")
            self._subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            self.layout().insertWidget(self.layout().count() - 1, self._subtitle_label, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            self._subtitle_label.setText(text)
