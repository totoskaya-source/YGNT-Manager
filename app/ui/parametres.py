from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTabWidget, QVBoxLayout, QWidget

from app.ui.producteurs import ProducteursPage


class ParametresPage(QWidget):
    def __init__(self) -> None:
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Parametres")
        title.setStyleSheet("font-size: 26px; font-weight: 700;")
        layout.addWidget(title)

        tabs = QTabWidget()
        tabs.addTab(ProducteursPage(), "Producteur")
        layout.addWidget(tabs)
