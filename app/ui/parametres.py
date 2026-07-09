from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget

from app.ui.about_dialog import AboutDialog
from app.ui.producteurs import ProducteursPage


class ParametresPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QHBoxLayout()

        title = QLabel("Parametres")
        title.setStyleSheet("font-size: 26px; font-weight: 700;")
        header.addWidget(title)
        header.addStretch()

        self.btn_about = QPushButton("A propos...")
        self.btn_about.clicked.connect(self.show_about)
        header.addWidget(self.btn_about)

        layout.addLayout(header)

        tabs = QTabWidget()
        tabs.addTab(ProducteursPage(), "Producteur")
        layout.addWidget(tabs)

    def show_about(self) -> None:
        AboutDialog(self).exec()
