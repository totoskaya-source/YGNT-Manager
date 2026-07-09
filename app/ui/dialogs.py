from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QMessageBox


def confirm_delete(parent: Any, label: str) -> bool:
    """Boite de confirmation de suppression uniforme dans tout le logiciel :
    meme titre, meme texte, memes boutons (Non par defaut)."""
    response = QMessageBox.question(
        parent,
        "Confirmation",
        f"Supprimer {label} ?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No,
    )
    return response == QMessageBox.StandardButton.Yes
