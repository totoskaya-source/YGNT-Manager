from PySide6.QtWidgets import QWidget, QPushButton, QLabel, QVBoxLayout


class Sidebar(QWidget):

    def __init__(self, callback):
        super().__init__()

        self.setFixedWidth(220)

        layout = QVBoxLayout(self)

        titre = QLabel("YGNT\nManager")
        titre.setStyleSheet("""
            font-size:24px;
            font-weight:bold;
            padding:20px;
        """)

        layout.addWidget(titre)

        pages = [
            ("🏠 Tableau de bord", "dashboard"),
            ("👥 Artistes", "artistes"),
            ("🏢 Organisateurs", "organisateurs"),
            ("🎤 Prestations", "prestations"),
            ("📄 Contrats", "contrats"),
            ("🧾 Devis", "devis"),
            ("💰 Factures", "factures"),
        ]

        for texte, page in pages:

            bouton = QPushButton(texte)

            bouton.clicked.connect(
                lambda checked=False, p=page: callback(p)
            )

            layout.addWidget(bouton)

        layout.addStretch()
        