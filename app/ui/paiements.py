from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
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

from app.models.paiement import Paiement
from app.services.facture_service import FactureService
from app.services.paiement_service import PaiementService
from app.ui.dialogs import confirm_delete
from app.ui.paiement_dialog import PaiementDialog
from app.ui.theme import DateTableWidgetItem, mark_destructive, style_page_title, style_table


class PaiementsPage(QWidget):
    HEADERS = (
        "ID",
        "Référence",
        "Date",
        "Facture",
        "Montant",
        "Mode de paiement",
        "Statut",
    )
    # Index de la colonne Date : trie chronologiquement via
    # DateTableWidgetItem plutot que comme du texte (v1.0.3, BUG-001).
    DATE_COLUMN = 2

    def __init__(
        self,
        service: PaiementService | None = None,
        facture_service: FactureService | None = None,
    ) -> None:
        super().__init__()

        self.service = service or PaiementService()
        self.facture_service = facture_service or FactureService()
        self._paiements: list[Paiement] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Paiements")
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
        self.table.itemDoubleClicked.connect(self.edit_selected_paiement)
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

        self.btn_add = QPushButton("Nouveau")
        self.btn_edit = QPushButton("Modifier")
        self.btn_delete = QPushButton("Supprimer")
        mark_destructive(self.btn_delete)
        self.btn_refresh = QPushButton("Actualiser")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher un paiement...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh_table)

        self.btn_add.clicked.connect(self.new_paiement)
        self.btn_edit.clicked.connect(self.edit_selected_paiement)
        self.btn_delete.clicked.connect(self.delete_selected_paiement)
        self.btn_refresh.clicked.connect(self.refresh_table)

        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_delete)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        toolbar.addWidget(self.search, 1)

        return toolbar

    def new_paiement(self) -> None:
        dialog = PaiementDialog(self, service=self.service, facture_service=self.facture_service)

        if dialog.exec():
            try:
                self.service.create_paiement(dialog.paiement)
            except ValueError as exc:
                QMessageBox.warning(self, "Paiement invalide", str(exc))
                return

            self.refresh_table()

    def edit_selected_paiement(self, *_args: Any) -> None:
        paiement_id = self._selected_paiement_id()

        if paiement_id is None:
            QMessageBox.information(self, "Modification", "Sélectionnez un paiement.")
            return

        paiement = self.service.get_paiement(paiement_id)

        if paiement is None:
            QMessageBox.warning(self, "Modification", "Ce paiement n'existe plus.")
            self.refresh_table()
            return

        dialog = PaiementDialog(
            self,
            paiement=paiement,
            service=self.service,
            facture_service=self.facture_service,
        )

        if dialog.exec():
            try:
                self.service.update_paiement(dialog.paiement)
            except ValueError as exc:
                QMessageBox.warning(self, "Paiement invalide", str(exc))
                return

            self.refresh_table()

    def delete_selected_paiement(self) -> None:
        paiement_id = self._selected_paiement_id()

        if paiement_id is None:
            QMessageBox.information(self, "Suppression", "Sélectionnez un paiement.")
            return

        paiement = self.service.get_paiement(paiement_id)
        label = paiement.reference if paiement and paiement.reference else "ce paiement"

        if confirm_delete(self, label):
            self.service.delete_paiement(paiement_id)
            self.refresh_table()

    def refresh_table(self) -> None:
        self._paiements = self.service.search_paiements(self.search.text())
        self._fill_table(self._paiements)
        self._sync_buttons()

    def _fill_table(self, paiements: list[Paiement]) -> None:
        factures_by_id = {facture.id: facture for facture in self.facture_service.list_factures()}

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(paiements))

        for row, paiement in enumerate(paiements):
            facture = factures_by_id.get(paiement.facture_id)
            values = (
                paiement.id,
                paiement.reference,
                paiement.date_paiement,
                facture.facture_number if facture else "",
                float(paiement.montant or 0),
                paiement.mode_paiement,
                paiement.status_label,
            )

            for column, value in enumerate(values):
                if column == self.DATE_COLUMN:
                    item = DateTableWidgetItem(value)
                else:
                    item = self._make_item(value)
                if column == 4:
                    item.setData(Qt.ItemDataRole.EditRole, float(value))
                    item.setText(f"{float(value):.2f} EUR")
                self.table.setItem(row, column, item)

        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def _make_item(self, value: Any) -> QTableWidgetItem:
        item = QTableWidgetItem("" if value is None else str(value))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _selected_paiement_id(self) -> int | None:
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

    def _sync_buttons(self) -> None:
        has_selection = self._selected_paiement_id() is not None
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)
