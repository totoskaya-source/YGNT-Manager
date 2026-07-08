from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout


class Dashboard(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        titre = QLabel("Tableau de bord")
        titre.setStyleSheet("""
            font-size:28px;
            font-weight:bold;
        """)

        layout.addWidget(titre)

        layout.addWidget(
            QLabel("Bienvenue dans YGNT Manager.")
        )

        layout.addStretch()
        