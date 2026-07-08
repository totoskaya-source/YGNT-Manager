from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLineEdit


class Toolbar(QWidget):

    def __init__(self):
        super().__init__()

        layout = QHBoxLayout(self)

        self.btn_add = QPushButton("➕ Ajouter")
        self.btn_edit = QPushButton("✏ Modifier")
        self.btn_delete = QPushButton("🗑 Supprimer")
        self.btn_refresh = QPushButton("🔄 Actualiser")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher...")

        layout.addWidget(self.btn_add)
        layout.addWidget(self.btn_edit)
        layout.addWidget(self.btn_delete)
        layout.addWidget(self.btn_refresh)

        layout.addStretch()

        layout.addWidget(self.search)
        