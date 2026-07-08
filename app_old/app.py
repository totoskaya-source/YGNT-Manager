from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout

from app.ui.sidebar import Sidebar
from app.ui.dashboard import Dashboard


class YGNTManager(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("YGNT Manager")
        self.resize(1400, 850)

        central = QWidget()
        self.setCentralWidget(central)

        self.layout = QHBoxLayout(central)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.sidebar = Sidebar(self.change_page)
        self.layout.addWidget(self.sidebar)

        self.page = Dashboard()
        self.layout.addWidget(self.page)

    def change_page(self, page_name):

        self.layout.removeWidget(self.page)
        self.page.deleteLater()

        if page_name == "dashboard":
            self.page = Dashboard()

        else:
            from PySide6.QtWidgets import QLabel
            from PySide6.QtCore import Qt

            self.page = QLabel(f"{page_name}\n\nEn cours de développement")
            self.page.setAlignment(Qt.AlignCenter)

        self.layout.addWidget(self.page)
        