from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt
from app.theme import get_base_stylesheet


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bilibili Personal Collect")
        self.resize(1200, 800)
        self.setStyleSheet(get_base_stylesheet())

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.title_label = QLabel("Bilibili Collection Manager")
        self.title_label.setObjectName("h1")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.title_label)

        self.start_button = QPushButton("Start App")
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.layout.addWidget(self.start_button)
