from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout

from app.ui.theme import style_dialog_title
from app.version import APP_AUTHOR, APP_COPYRIGHT, APP_NAME, APP_VERSION, APP_WEBSITE


class AboutDialog(QDialog):
    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)

        self.setWindowTitle("À propos")
        self.setFixedSize(360, 240)

        layout = QVBoxLayout(self)

        title = QLabel(APP_NAME)
        style_dialog_title(title)
        layout.addWidget(title)

        layout.addWidget(QLabel(f"Version {APP_VERSION}"))
        layout.addWidget(QLabel(f"Auteur : {APP_AUTHOR}"))

        if APP_WEBSITE:
            layout.addWidget(QLabel(f"Site internet : {APP_WEBSITE}"))

        copyright_label = QLabel(APP_COPYRIGHT)
        copyright_label.setWordWrap(True)
        layout.addWidget(copyright_label)
        layout.addStretch()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
