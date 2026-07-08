from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QWidget,
)

from app.ui.artistes import ArtistesPage
from app.ui.contracts import ContractsPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("YGNT Manager")
        self.resize(1400, 850)

        central = QWidget()
        self.setCentralWidget(central)

        self.main_layout = QHBoxLayout()
        central.setLayout(self.main_layout)

        # ===== Menu =====

        self.menu = QListWidget()
        self.menu.setFixedWidth(220)

        self.menu.addItems([
            "🏠 Tableau de bord",
            "👥 Artistes",
            "📄 Contrats",
            "🏢 Organisateurs",
            "🎤 Prestations",
            "🧾 Devis",
            "💰 Factures",
            "⚙️ Paramètres",
        ])

        self.main_layout.addWidget(self.menu)

        # ===== Zone centrale =====

        self.page = QLabel("Bienvenue dans YGNT Manager")
        self.page.setAlignment(Qt.AlignCenter)
        self.page.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
        """)

        self.main_layout.addWidget(self.page)

        self.menu.currentTextChanged.connect(self.change_page)
        self.menu.setCurrentRow(0)

    def change_page(self, page):

        self.main_layout.removeWidget(self.page)
        self.page.deleteLater()

        if "Artistes" in page:
            self.page = ArtistesPage()

        elif "Contrats" in page:
            self.page = ContractsPage()

        else:
            self.page = QLabel(page)
            self.page.setAlignment(Qt.AlignCenter)
            self.page.setStyleSheet("""
                font-size:28px;
                font-weight:bold;
            """)

        self.main_layout.addWidget(self.page)
        