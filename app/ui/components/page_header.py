"""PageHeader — page-level title with optional subtitle."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

from app.theme import Spacing


class PageHeader(QWidget):
    """Top-of-page heading widget.

    Displays a serif title and an optional smaller subtitle beneath it.
    Styled via object-name selectors in the base stylesheet.
    """

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)

        self._title_label = QLabel(title)
        self._title_label.setObjectName("page-header-title")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.SCALE_4)
        layout.addWidget(self._title_label)

        self._subtitle_label: QLabel | None = None
        if subtitle:
            self._subtitle_label = QLabel(subtitle)
            self._subtitle_label.setObjectName("page-header-subtitle")
            layout.addWidget(self._subtitle_label)

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
            self._subtitle_label.setObjectName("page-header-subtitle")
            self.layout().addWidget(self._subtitle_label)
        else:
            self._subtitle_label.setText(text)
