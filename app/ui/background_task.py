"""Execution d'un traitement long (ex. generation PDF via Word COM) hors du
thread graphique Qt, avec un dialogue de progression non bloquant. Reutilise
par les dialogues Contrat, Devis et Facture pour eviter toute duplication."""

from __future__ import annotations

from typing import Any, Callable

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QVBoxLayout, QWidget


class BackgroundTaskWorker(QThread):
    """Execute `task` (une fonction sans argument) sur un thread separe.
    Emet `succeeded` avec le resultat, ou `failed` avec l'exception levee -
    jamais d'exception propagee sur le thread graphique."""

    succeeded = Signal(object)
    failed = Signal(object)

    def __init__(self, task: Callable[[], Any], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._task = task

    def run(self) -> None:
        try:
            result = self._task()
        except Exception as exc:  # noqa: BLE001 - remontee a l'appelant via signal
            self.failed.emit(exc)
            return
        self.succeeded.emit(result)


class ProgressDialog(QDialog):
    """Petite fenêtre "Veuillez patienter" avec barre de progression
    indeterminee, affichee pendant qu'un BackgroundTaskWorker travaille.
    Sans bouton de fermeture : l'utilisateur ne peut pas la refermer avant
    la fin du traitement (succes, erreur ou timeout)."""

    def __init__(self, parent: QWidget | None, message: str) -> None:
        super().__init__(parent)
        self.setWindowTitle("Veuillez patienter")
        self.setModal(True)
        self.setFixedSize(340, 120)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.CustomizeWindowHint
            | Qt.WindowType.WindowTitleHint
        )

        label = QLabel(message)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        progress = QProgressBar()
        progress.setRange(0, 0)  # barre indeterminee : aucune estimation de duree fiable

        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(label)
        layout.addWidget(progress)
        layout.addStretch()


def run_task_with_progress(
    parent: QWidget,
    message: str,
    task: Callable[[], Any],
    on_success: Callable[[Any], None],
    on_error: Callable[[Exception], None],
) -> None:
    """Lance `task` dans un BackgroundTaskWorker pendant qu'un ProgressDialog
    est affiche. L'interface reste reactive : seul ce petit dialogue est
    modal, le traitement (ex. Word COM) ne touche jamais le thread graphique.
    Appelle `on_success`/`on_error` sur le thread graphique une fois termine."""
    dialog = ProgressDialog(parent, message)
    worker = BackgroundTaskWorker(task, parent)

    def _handle_success(result: Any) -> None:
        dialog.accept()
        on_success(result)

    def _handle_failure(exc: Exception) -> None:
        dialog.reject()
        on_error(exc)

    worker.succeeded.connect(_handle_success)
    worker.failed.connect(_handle_failure)
    worker.finished.connect(worker.deleteLater)

    worker.start()
    dialog.exec()
