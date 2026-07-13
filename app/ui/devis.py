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

from app.models.devis import Devis
from app.services.artist_service import ArtistService
from app.services.contract_service import ContractService
from app.services.devis_service import DevisService
from app.services.organization_service import OrganizationService
from app.ui.contract_dialog import ContractDialog
from app.ui.devis_dialog import DevisDialog
from app.ui.dialogs import confirm_delete
from app.ui.theme import mark_destructive, style_page_title, style_table


class DevisPage(QWidget):
    HEADERS = (
        "ID",
        "Reference",
        "Date",
        "Formation",
        "Organisateur",
        "Objet",
        "Montant",
        "Statut",
    )

    def __init__(
        self,
        service: DevisService | None = None,
        contract_service: ContractService | None = None,
        artist_service: ArtistService | None = None,
        organization_service: OrganizationService | None = None,
    ) -> None:
        super().__init__()

        self.service = service or DevisService()
        self.contract_service = contract_service or ContractService()
        self.artist_service = artist_service or ArtistService()
        self.organization_service = organization_service or OrganizationService()
        self._devis: list[Devis] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Devis")
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
        self.table.itemDoubleClicked.connect(self.edit_selected_devis)
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
        self.btn_create_contract = QPushButton("Creer un contrat")
        self.btn_refresh = QPushButton("Actualiser")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher un devis...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh_table)

        self.btn_add.clicked.connect(self.new_devis)
        self.btn_edit.clicked.connect(self.edit_selected_devis)
        self.btn_delete.clicked.connect(self.delete_selected_devis)
        self.btn_create_contract.clicked.connect(self.create_contract_from_selected_devis)
        self.btn_refresh.clicked.connect(self.refresh_table)

        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_delete)
        toolbar.addWidget(self.btn_create_contract)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        toolbar.addWidget(self.search, 1)

        return toolbar

    def new_devis(self) -> None:
        # Le dialogue s'enregistre desormais lui-meme (Sprint 12.0) : il reste
        # ouvert apres la creation pour generer immediatement DOCX/PDF, sans
        # repasser par cette liste. On se contente de rafraichir au retour.
        dialog = DevisDialog(self, service=self.service)
        dialog.exec()
        self.refresh_table()

    def edit_selected_devis(self, *_args: Any) -> None:
        devis_id = self._selected_devis_id()

        if devis_id is None:
            QMessageBox.information(self, "Modification", "Selectionnez un devis.")
            return

        devis = self.service.get_devis(devis_id)

        if devis is None:
            QMessageBox.warning(self, "Modification", "Ce devis n'existe plus.")
            self.refresh_table()
            return

        dialog = DevisDialog(self, devis=devis, service=self.service)
        dialog.exec()
        self.refresh_table()

    def delete_selected_devis(self) -> None:
        devis_id = self._selected_devis_id()

        if devis_id is None:
            QMessageBox.information(self, "Suppression", "Selectionnez un devis.")
            return

        devis = self.service.get_devis(devis_id)
        label = devis.devis_number if devis and devis.devis_number else "ce devis"

        if confirm_delete(self, label):
            self.service.delete_devis(devis_id)
            self.refresh_table()

    def create_contract_from_selected_devis(self) -> None:
        devis_id = self._selected_devis_id()

        if devis_id is None:
            QMessageBox.information(self, "Creer un contrat", "Selectionnez un devis.")
            return

        devis = self.service.get_devis(devis_id)

        if devis is None:
            QMessageBox.warning(self, "Creer un contrat", "Ce devis n'existe plus.")
            self.refresh_table()
            return

        if devis.status != "accepted":
            QMessageBox.information(
                self,
                "Creer un contrat",
                "Seul un devis au statut 'Accepte' peut etre transforme en contrat.",
            )
            return

        # Le devis n'est jamais modifie : le contrat est un nouveau document
        # independant, pre-rempli puis toujours modifiable avant enregistrement.
        seed = self.contract_service.build_from_devis(devis)

        dialog = ContractDialog(
            self,
            initial_contract=seed,
            service=self.contract_service,
            artist_service=self.artist_service,
            organization_service=self.organization_service,
        )
        dialog.exec()

    def refresh_table(self) -> None:
        self._devis = self.service.search_devis(self.search.text())
        self._fill_table(self._devis)
        self._sync_buttons()

    def _fill_table(self, devis_list: list[Devis]) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(devis_list))

        for row, devis in enumerate(devis_list):
            values = (
                devis.id,
                devis.devis_number,
                devis.prestation_date,
                devis.formation_nom,
                devis.organisateur_structure,
                devis.spectacle_nom,
                float(devis.montant or 0),
                devis.status_label,
            )

            for column, value in enumerate(values):
                item = self._make_item(value)
                if column == 6:
                    # L'ordre importe : EditRole doit etre fixe avant le texte
                    # affiche, sinon Qt reaffiche la valeur brute (voir tests).
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

    def _selected_devis_id(self) -> int | None:
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
        devis_id = self._selected_devis_id()
        has_selection = devis_id is not None
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)

        selected = next((d for d in self._devis if d.id == devis_id), None)
        self.btn_create_contract.setEnabled(bool(selected and selected.status == "accepted"))
