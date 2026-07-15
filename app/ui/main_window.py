from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QWidget,
)

from app.ui.artistes import ArtistesPage
from app.ui.cddu import CdduPage
from app.ui.contracts import ContractsPage
from app.ui.dashboard import DashboardPage
from app.ui.devis import DevisPage
from app.ui.factures import FacturesPage
from app.ui.formations import FormationsPage
from app.ui.organisateurs import OrganisateursPage
from app.ui.paiements import PaiementsPage
from app.ui.parametres import ParametresPage
from app.ui.prestations import PrestationsPage
from app.ui.statistiques import StatistiquesPage
from app.ui.theme import SIDEBAR_WIDTH, style_page_title, style_sidebar
from app.version import APP_NAME, APP_VERSION


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(1400, 850)

        self.statusBar().addPermanentWidget(QLabel(f"Version {APP_VERSION}"))

        central = QWidget()
        self.setCentralWidget(central)

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        central.setLayout(self.main_layout)

        # ===== Menu =====

        self.menu = QListWidget()
        self.menu.setFixedWidth(SIDEBAR_WIDTH)
        style_sidebar(self.menu)

        self.menu.addItems([
            "🏠 Tableau de bord",
            "📊 Statistiques",
            "🎭 Prestations",
            "👤 Artistes",
            "🎼 Formations",
            "🏢 Organisateurs",
            "📄 Devis",
            "📃 Contrats",
            "📝 CDDU",
            "🧾 Factures",
            "💳 Paiements",
            "⚙ Paramètres",
        ])

        self.main_layout.addWidget(self.menu)

        # ===== Zone centrale =====

        self.page = QLabel("Bienvenue dans YGNT Manager")
        self.page.setAlignment(Qt.AlignCenter)
        style_page_title(self.page)

        self.main_layout.addWidget(self.page)

        self.menu.currentTextChanged.connect(self.change_page)
        self.menu.setCurrentRow(0)

    def change_page(self, page):

        self.main_layout.removeWidget(self.page)
        self.page.deleteLater()

        if "Tableau de bord" in page:
            self.page = DashboardPage()

        elif "Statistiques" in page:
            self.page = StatistiquesPage()

        elif "Prestations" in page:
            self.page = PrestationsPage()

        elif "Artistes" in page:
            self.page = ArtistesPage()

        elif "Formations" in page:
            self.page = FormationsPage()

        elif "Devis" in page:
            self.page = DevisPage()

        elif "Contrats" in page:
            self.page = ContractsPage()

        elif "CDDU" in page:
            self.page = CdduPage()

        elif "Factures" in page:
            self.page = FacturesPage()

        elif "Paiements" in page:
            self.page = PaiementsPage()

        elif "Organisateurs" in page:
            self.page = OrganisateursPage()

        elif "Paramètres" in page:
            self.page = ParametresPage()

        else:
            self.page = QLabel(page)
            self.page.setAlignment(Qt.AlignCenter)
            style_page_title(self.page)

        self.main_layout.addWidget(self.page)
        