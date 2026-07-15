from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget

from app.ui.about_dialog import AboutDialog
from app.ui.producteurs import ProducteursPage
from app.ui.theme import style_page_title


class ParametresPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()

        title = QLabel("Paramètres")
        style_page_title(title)
        header.addWidget(title)
        header.addStretch()

        self.btn_about = QPushButton("À propos...")
        self.btn_about.clicked.connect(self.show_about)
        header.addWidget(self.btn_about)

        layout.addLayout(header)

        tabs = QTabWidget()
        tabs.addTab(ProducteursPage(), "Producteurs")
        layout.addWidget(tabs)

    def show_about(self) -> None:
        AboutDialog(self).exec()
