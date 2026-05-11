"""LogPanel — read-only text area for log output with auto-scroll."""

from PySide6.QtWidgets import QSizePolicy, QTextEdit, QVBoxLayout, QWidget


class LogPanel(QWidget):
    """Wraps a read-only QTextEdit for log output.

    Provides ``append_log(message)`` and ``clear_logs()`` methods.
    Auto-scrolls to the bottom on new messages.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("log-panel")

        self._text_edit = QTextEdit()
        self._text_edit.setReadOnly(True)
        self._text_edit.setObjectName("log-panel-text-edit")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._text_edit)

        self.setMinimumHeight(100)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    @property
    def text_edit(self) -> QTextEdit:
        return self._text_edit

    def append_log(self, message: str) -> None:
        self._text_edit.append(message)
        # Auto-scroll to bottom
        scrollbar = self._text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear_logs(self) -> None:
        self._text_edit.clear()
