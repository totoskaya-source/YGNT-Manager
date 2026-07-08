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

from app.models.prestation import Prestation
from app.services.artist_service import ArtistService
from app.services.contract_service import ContractService
from app.services.organization_service import OrganizationService
from app.services.prestation_service import PrestationService
from app.ui.contract_dialog import ContractDialog
from app.ui.prestation_dialog import PrestationDialog


class PrestationsPage(QWidget):
    HEADERS = (
        "ID",
        "Reference",
        "Date",
        "Nom",
        "Type",
        "Artiste",
        "Organisateur",
        "Lieu",
        "Statut",
    )

    def __init__(
        self,
        service: PrestationService | None = None,
        artist_service: ArtistService | None = None,
        organization_service: OrganizationService | None = None,
        contract_service: ContractService | None = None,
    ) -> None:
        super().__init__()

        self.service = service or PrestationService()
        self.artist_service = artist_service or ArtistService()
        self.organization_service = organization_service or OrganizationService()
        self.contract_service = contract_service or ContractService()
        self._prestations: list[Prestation] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Prestations")
        title.setStyleSheet("font-size: 26px; font-weight: 700;")
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
        self.table.itemDoubleClicked.connect(self.edit_selected_prestation)
        self.table.itemSelectionChanged.connect(self._sync_buttons)

        header = self.table.horizontalHeader()
        header.setSortIndicatorShown(True)
        header.setSectionsClickable(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
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
        self.btn_create_contract = QPushButton("Creer un contrat")
        self.btn_refresh = QPushButton("Actualiser")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher une prestation...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh_table)

        self.btn_add.clicked.connect(self.new_prestation)
        self.btn_edit.clicked.connect(self.edit_selected_prestation)
        self.btn_delete.clicked.connect(self.delete_selected_prestation)
        self.btn_create_contract.clicked.connect(self.create_contract_from_selected_prestation)
        self.btn_refresh.clicked.connect(self.refresh_table)

        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_delete)
        toolbar.addWidget(self.btn_create_contract)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        toolbar.addWidget(self.search, 1)

        return toolbar

    def new_prestation(self) -> None:
        dialog = PrestationDialog(
            self,
            service=self.service,
            artist_service=self.artist_service,
            organization_service=self.organization_service,
        )

        if dialog.exec():
            try:
                self.service.create_prestation(dialog.prestation)
            except ValueError as exc:
                QMessageBox.warning(self, "Prestation invalide", str(exc))
                return

            self.refresh_table()

    def edit_selected_prestation(self, *_args: Any) -> None:
        prestation_id = self._selected_prestation_id()

        if prestation_id is None:
            QMessageBox.information(self, "Modification", "Selectionnez une prestation.")
            return

        prestation = self.service.get_prestation(prestation_id)

        if prestation is None:
            QMessageBox.warning(self, "Modification", "Cette prestation n'existe plus.")
            self.refresh_table()
            return

        dialog = PrestationDialog(
            self,
            prestation=prestation,
            service=self.service,
            artist_service=self.artist_service,
            organization_service=self.organization_service,
        )

        if dialog.exec():
            try:
                self.service.update_prestation(dialog.prestation)
            except ValueError as exc:
                QMessageBox.warning(self, "Prestation invalide", str(exc))
                return

            self.refresh_table()

    def delete_selected_prestation(self) -> None:
        prestation_id = self._selected_prestation_id()

        if prestation_id is None:
            QMessageBox.information(self, "Suppression", "Selectionnez une prestation.")
            return

        prestation = self.service.get_prestation(prestation_id)
        label = prestation.nom if prestation and prestation.nom else "cette prestation"

        response = QMessageBox.question(
            self,
            "Confirmation",
            f"Supprimer {label} ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if response == QMessageBox.StandardButton.Yes:
            self.service.delete_prestation(prestation_id)
            self.refresh_table()

    def create_contract_from_selected_prestation(self) -> None:
        prestation_id = self._selected_prestation_id()

        if prestation_id is None:
            QMessageBox.information(self, "Creer un contrat", "Selectionnez une prestation.")
            return

        prestation = self.service.get_prestation(prestation_id)

        if prestation is None:
            QMessageBox.warning(self, "Creer un contrat", "Cette prestation n'existe plus.")
            self.refresh_table()
            return

        seed = self.contract_service.build_from_prestation(prestation)

        dialog = ContractDialog(
            self,
            initial_contract=seed,
            service=self.contract_service,
            artist_service=self.artist_service,
            organization_service=self.organization_service,
        )

        if dialog.exec():
            try:
                self.contract_service.create_contract(dialog.contract)
            except ValueError as exc:
                QMessageBox.warning(self, "Contrat invalide", str(exc))
                return

            QMessageBox.information(
                self,
                "Contrat cree",
                f"Contrat {dialog.contract.contract_number} cree pour cette prestation.",
            )

    def refresh_table(self) -> None:
        self._prestations = self.service.search_prestations(self.search.text())
        self._fill_table(self._prestations)
        self._sync_buttons()

    def _fill_table(self, prestations: list[Prestation]) -> None:
        artist_labels = {
            artist.id: (artist.stage_name or artist.legal_name or "")
            for artist in self.artist_service.list_artists()
        }
        organization_labels = {
            organization.id: (organization.name or "")
            for organization in self.organization_service.list_organizations()
        }

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(prestations))

        for row, prestation in enumerate(prestations):
            values = (
                prestation.id,
                prestation.reference,
                self._format_dates(prestation),
                prestation.nom,
                prestation.type_evenement,
                artist_labels.get(prestation.artist_id, ""),
                organization_labels.get(prestation.organization_id, ""),
                prestation.lieu_nom or prestation.lieu_city,
                prestation.statut_label,
            )

            for column, value in enumerate(values):
                self.table.setItem(row, column, self._make_item(value))

        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def _format_dates(self, prestation: Prestation) -> str:
        if prestation.date_fin and prestation.date_fin != prestation.date_debut:
            return f"{prestation.date_debut} - {prestation.date_fin}"
        return prestation.date_debut

    def _make_item(self, value: Any) -> QTableWidgetItem:
        item = QTableWidgetItem("" if value is None else str(value))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _selected_prestation_id(self) -> int | None:
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
        has_selection = self._selected_prestation_id() is not None
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)
        self.btn_create_contract.setEnabled(has_selection)
