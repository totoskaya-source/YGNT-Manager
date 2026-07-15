from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.models.contrat_cddu import ContratCddu
from app.services.contrat_cddu_service import ContratCdduService
from app.ui.cddu_dialog import CdduDialog
from app.ui.dialogs import confirm_delete, notify_error, notify_success
from app.ui.theme import DateTableWidgetItem, mark_destructive, style_page_title, style_table


class CdduPage(QWidget):
    """Liste des Contrats de travail (CDDU) - Sprint 17.0. Meme ergonomie que
    ContractsPage : recherche, tableau, double-clic pour modifier."""

    HEADERS = (
        "ID",
        "Référence",
        "Artiste",
        "Prestation",
        "Date",
        "Statut",
        "PDF",
    )
    # Index de la colonne Date : trie chronologiquement via
    # DateTableWidgetItem plutot que comme du texte (v1.0.3, BUG-001).
    DATE_COLUMN = 4

    def __init__(self, service: ContratCdduService | None = None) -> None:
        super().__init__()

        self.service = service or ContratCdduService()
        self._contrats: list[ContratCddu] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("CDDU")
        style_page_title(title)
        layout.addWidget(title)

        layout.addLayout(self._build_toolbar())

        self.table = QTableWidget()
        self.table.setColumnCount(len(self.HEADERS))
        self.table.setHorizontalHeaderLabels(self.HEADERS)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setColumnHidden(0, True)
        self.table.itemDoubleClicked.connect(self.edit_selected_contrat)
        self.table.itemSelectionChanged.connect(self._sync_buttons)
        style_table(self.table)

        header = self.table.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)

        layout.addWidget(self.table)

        self.refresh_table()
        self._sync_buttons()

    def _build_toolbar(self) -> QHBoxLayout:
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.btn_new = QPushButton("Nouveau CDDU")
        self.btn_edit = QPushButton("Modifier")
        self.btn_delete = QPushButton("Supprimer")
        mark_destructive(self.btn_delete)
        self.btn_refresh = QPushButton("Actualiser")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher un CDDU...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh_table)

        self.status_filter = QComboBox()
        self.status_filter.addItem("Tous les statuts", "all")
        self.status_filter.addItem("Brouillon", "draft")
        self.status_filter.addItem("Validé", "validated")
        self.status_filter.addItem("PDF généré", "pdf_generated")
        self.status_filter.currentIndexChanged.connect(self.refresh_table)

        self.btn_new.clicked.connect(self.new_contrat)
        self.btn_edit.clicked.connect(self.edit_selected_contrat)
        self.btn_delete.clicked.connect(self.delete_selected_contrat)
        self.btn_refresh.clicked.connect(self.refresh_table)

        for button in (self.btn_new, self.btn_edit, self.btn_delete, self.btn_refresh):
            toolbar.addWidget(button)

        toolbar.addStretch()
        toolbar.addWidget(self.status_filter)
        toolbar.addWidget(self.search, 1)
        return toolbar

    def new_contrat(self) -> None:
        dialog = CdduDialog(self, service=self.service)
        dialog.exec()
        self.refresh_table()

    def edit_selected_contrat(self, *_args: Any) -> None:
        contrat = self._selected_contrat()

        if contrat is None:
            QMessageBox.information(self, "Modification", "Sélectionnez un CDDU.")
            return

        dialog = CdduDialog(self, contrat=contrat, service=self.service)
        dialog.exec()
        self.refresh_table()

    def delete_selected_contrat(self) -> None:
        contrat = self._selected_contrat()

        if contrat is None or contrat.id is None:
            QMessageBox.information(self, "Suppression", "Sélectionnez un CDDU.")
            return

        label = f"le CDDU {contrat.numero or contrat.id}"

        if confirm_delete(self, label):
            self._run_action(
                lambda: self.service.delete_contrat(int(contrat.id)),
                "CDDU supprimé.",
            )
            self.refresh_table()

    def refresh_table(self) -> None:
        status = str(self.status_filter.currentData())
        self._contrats = self.service.search_contrats(self.search.text(), status)
        self._fill_table(self._contrats)
        self._sync_buttons()

    def _fill_table(self, contrats: list[ContratCddu]) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(contrats))

        for row, contrat in enumerate(contrats):
            date_debut = ""
            if contrat.id is not None:
                date_debut, _ = self.service.date_range(contrat.id)

            values = (
                contrat.id,
                contrat.numero,
                contrat.artiste_nom,
                contrat.prestation_reference,
                date_debut,
                contrat.status_label,
                self._path_state(contrat.pdf_path),
            )

            for column, value in enumerate(values):
                if column == self.DATE_COLUMN:
                    item = DateTableWidgetItem(value)
                else:
                    item = self._make_item(value)
                self.table.setItem(row, column, item)

        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def _make_item(self, value: Any) -> QTableWidgetItem:
        item = QTableWidgetItem("" if value is None else str(value))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _selected_contrat_id(self) -> int | None:
        row = self.table.currentRow()
        if row < 0:
            return None

        item = self.table.item(row, 0)
        if item is None:
            return None

        try:
            return int(item.text())
        except ValueError:
            return None

    def _selected_contrat(self) -> ContratCddu | None:
        contrat_id = self._selected_contrat_id()
        return self.service.get_contrat(contrat_id) if contrat_id is not None else None

    def _sync_buttons(self) -> None:
        has_selection = self._selected_contrat_id() is not None
        for button in (self.btn_edit, self.btn_delete):
            button.setEnabled(has_selection)

    def _path_state(self, path: str) -> str:
        return "Oui" if path and Path(path).exists() else "Non"

    def _run_action(self, action: Callable[[], Any], success_message: str) -> Any:
        try:
            result = action()
        except Exception as exc:
            notify_error(self, str(exc))
            return None

        if success_message:
            notify_success(self, success_message)
        return result
