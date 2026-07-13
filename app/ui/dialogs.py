from __future__ import annotations

import os
from pathlib import Path
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


def notify_success(parent: Any, message: str) -> None:
    """Confirmation de succes uniforme dans tout le logiciel : meme titre,
    meme style, pour toute action reussie (creation, modification,
    generation de document, enregistrement d'un paiement...)."""
    QMessageBox.information(parent, "Succes", message)


def open_folder(path: Path) -> None:
    """Ouvre un dossier dans l'explorateur de fichiers, en le creant d'abord
    s'il n'existe pas encore (ex. dossier exports/ jamais utilise)."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    os.startfile(path)
