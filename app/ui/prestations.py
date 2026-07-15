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
from app.services.contrat_cddu_service import ContratCdduService
from app.services.devis_service import DevisService
from app.services.facture_service import FactureService
from app.services.formation_artiste_service import FormationArtisteService
from app.services.organization_service import OrganizationService
from app.services.prestation_participant_service import PrestationParticipantService
from app.services.prestation_service import PrestationService
from app.ui.cddu_dialog import CdduDialog
from app.ui.contract_dialog import ContractDialog
from app.ui.devis_dialog import DevisDialog
from app.ui.dialogs import confirm_delete
from app.ui.facture_dialog import FactureDialog
from app.ui.intermipaie_dialog import IntermiPaieDialog
from app.ui.prestation_dialog import PrestationDialog
from app.ui.theme import DateTableWidgetItem, mark_destructive, style_page_title, style_table


class PrestationsPage(QWidget):
    HEADERS = (
        "ID",
        "Référence",
        "Date",
        "Nom",
        "Type",
        "Artiste",
        "Organisateur",
        "Lieu",
        "Statut",
    )
    # Index de la colonne Date dans HEADERS : trie chronologiquement via
    # DateTableWidgetItem plutot que comme du texte (v1.0.3, BUG-001).
    DATE_COLUMN = 2

    def __init__(
        self,
        service: PrestationService | None = None,
        artist_service: ArtistService | None = None,
        organization_service: OrganizationService | None = None,
        contract_service: ContractService | None = None,
        devis_service: DevisService | None = None,
        facture_service: FactureService | None = None,
        cddu_service: ContratCdduService | None = None,
        formation_composition_service: FormationArtisteService | None = None,
        participant_service: PrestationParticipantService | None = None,
    ) -> None:
        super().__init__()

        self.service = service or PrestationService()
        self.artist_service = artist_service or ArtistService()
        self.organization_service = organization_service or OrganizationService()
        self.contract_service = contract_service or ContractService()
        self.devis_service = devis_service or DevisService()
        self.facture_service = facture_service or FactureService()
        self.cddu_service = cddu_service or ContratCdduService()
        self.formation_composition_service = formation_composition_service or FormationArtisteService()
        self.participant_service = participant_service or PrestationParticipantService()
        self._prestations: list[Prestation] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Prestations")
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
        self.table.itemDoubleClicked.connect(self.edit_selected_prestation)
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
        self.btn_create_contract = QPushButton("Créer un contrat")
        self.btn_create_devis = QPushButton("Créer un devis")
        self.btn_create_facture = QPushButton("Créer une facture")
        self.btn_create_cddu = QPushButton("Créer un CDDU")
        self.btn_intermipaie = QPushButton("Calculer avec IntermiPaie")
        self.btn_refresh = QPushButton("Actualiser")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher une prestation...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh_table)

        self.btn_add.clicked.connect(self.new_prestation)
        self.btn_edit.clicked.connect(self.edit_selected_prestation)
        self.btn_delete.clicked.connect(self.delete_selected_prestation)
        self.btn_create_contract.clicked.connect(self.create_contract_from_selected_prestation)
        self.btn_create_devis.clicked.connect(self.create_devis_from_selected_prestation)
        self.btn_create_facture.clicked.connect(self.create_facture_from_selected_prestation)
        self.btn_create_cddu.clicked.connect(self.create_cddu_from_selected_prestation)
        self.btn_intermipaie.clicked.connect(self.open_intermipaie_for_selected_prestation)
        self.btn_refresh.clicked.connect(self.refresh_table)

        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_delete)
        toolbar.addWidget(self.btn_create_contract)
        toolbar.addWidget(self.btn_create_devis)
        toolbar.addWidget(self.btn_create_facture)
        toolbar.addWidget(self.btn_create_cddu)
        toolbar.addWidget(self.btn_intermipaie)
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
            devis_service=self.devis_service,
            contract_service=self.contract_service,
            facture_service=self.facture_service,
        )

        if dialog.exec():
            try:
                new_id = self.service.create_prestation(dialog.prestation)
            except ValueError as exc:
                QMessageBox.warning(self, "Prestation invalide", str(exc))
                return

            # Formation choisie sur une prestation toute neuve : premiere
            # sauvegarde, copie systematique de sa composition (rien a
            # ecraser puisqu'aucune equipe n'existait avant).
            if dialog.prestation.formation_id is not None:
                self._copy_formation_members(new_id, dialog.prestation.formation_id)

            self.refresh_table()

    def edit_selected_prestation(self, *_args: Any) -> None:
        prestation_id = self._selected_prestation_id()

        if prestation_id is None:
            QMessageBox.information(self, "Modification", "Sélectionnez une prestation.")
            return

        prestation = self.service.get_prestation(prestation_id)

        if prestation is None:
            QMessageBox.warning(self, "Modification", "Cette prestation n'existe plus.")
            self.refresh_table()
            return

        previous_formation_id = prestation.formation_id

        dialog = PrestationDialog(
            self,
            prestation=prestation,
            service=self.service,
            artist_service=self.artist_service,
            organization_service=self.organization_service,
            devis_service=self.devis_service,
            contract_service=self.contract_service,
            facture_service=self.facture_service,
        )

        if dialog.exec():
            try:
                self.service.update_prestation(dialog.prestation)
            except ValueError as exc:
                QMessageBox.warning(self, "Prestation invalide", str(exc))
                return

            # La copie ne se declenche que sur un veritable CHANGEMENT de
            # Formation, jamais a chaque sauvegarde : sinon un membre retire
            # manuellement de l'equipe serait systematiquement reajoute au
            # sauvegarde suivant (docs/PRESTATIONS_ARCHITECTURE.md, Sprint 18.0).
            if (
                dialog.prestation.formation_id is not None
                and dialog.prestation.formation_id != previous_formation_id
            ):
                self._copy_formation_members(dialog.prestation.id, dialog.prestation.formation_id)

            self.refresh_table()

    def _copy_formation_members(self, prestation_id: int, formation_id: int) -> None:
        for member in self.formation_composition_service.list_composition(formation_id):
            try:
                self.participant_service.add_participant(
                    prestation_id,
                    member.artiste_id,
                    role=member.role,
                    ordre=member.ordre,
                )
            except ValueError:
                pass  # deja participant : rien a faire (ne remplace jamais un retrait manuel)

    def delete_selected_prestation(self) -> None:
        prestation_id = self._selected_prestation_id()

        if prestation_id is None:
            QMessageBox.information(self, "Suppression", "Sélectionnez une prestation.")
            return

        prestation = self.service.get_prestation(prestation_id)
        label = prestation.nom if prestation and prestation.nom else "cette prestation"

        if confirm_delete(self, label):
            self.service.delete_prestation(prestation_id)
            self.refresh_table()

    def create_contract_from_selected_prestation(self) -> None:
        prestation_id = self._selected_prestation_id()

        if prestation_id is None:
            QMessageBox.information(self, "Créer un contrat", "Sélectionnez une prestation.")
            return

        prestation = self.service.get_prestation(prestation_id)

        if prestation is None:
            QMessageBox.warning(self, "Créer un contrat", "Cette prestation n'existe plus.")
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
        dialog.exec()

    def create_devis_from_selected_prestation(self) -> None:
        prestation_id = self._selected_prestation_id()

        if prestation_id is None:
            QMessageBox.information(self, "Créer un devis", "Sélectionnez une prestation.")
            return

        prestation = self.service.get_prestation(prestation_id)

        if prestation is None:
            QMessageBox.warning(self, "Créer un devis", "Cette prestation n'existe plus.")
            self.refresh_table()
            return

        seed = self.devis_service.build_from_prestation(prestation)

        dialog = DevisDialog(
            self,
            initial_devis=seed,
            service=self.devis_service,
            organization_service=self.organization_service,
        )
        dialog.exec()

    def create_facture_from_selected_prestation(self) -> None:
        prestation_id = self._selected_prestation_id()

        if prestation_id is None:
            QMessageBox.information(self, "Créer une facture", "Sélectionnez une prestation.")
            return

        prestation = self.service.get_prestation(prestation_id)

        if prestation is None:
            QMessageBox.warning(self, "Créer une facture", "Cette prestation n'existe plus.")
            self.refresh_table()
            return

        # La prestation n'est jamais modifiee : la facture est un nouveau
        # document independant, pre-rempli puis toujours modifiable avant
        # enregistrement (meme principe que Devis/Contrat depuis Prestation).
        seed = self.facture_service.build_from_prestation(prestation)

        dialog = FactureDialog(
            self,
            initial_facture=seed,
            service=self.facture_service,
            organization_service=self.organization_service,
        )
        dialog.exec()

    def create_cddu_from_selected_prestation(self) -> None:
        prestation_id = self._selected_prestation_id()

        if prestation_id is None:
            QMessageBox.information(self, "Créer un CDDU", "Sélectionnez une prestation.")
            return

        prestation = self.service.get_prestation(prestation_id)

        if prestation is None:
            QMessageBox.warning(self, "Créer un CDDU", "Cette prestation n'existe plus.")
            self.refresh_table()
            return

        # Meme ergonomie que Devis/Contrat/Facture : la prestation n'est
        # jamais modifiee, le CDDU reste un nouveau document independant,
        # pre-selectionne sur cette prestation puis toujours modifiable
        # avant enregistrement (artiste, defraiements...).
        dialog = CdduDialog(
            self,
            service=self.cddu_service,
            artist_service=self.artist_service,
            organization_service=self.organization_service,
            participant_service=self.participant_service,
            formation_composition_service=self.formation_composition_service,
            initial_prestation_id=prestation_id,
        )
        dialog.exec()

    def open_intermipaie_for_selected_prestation(self) -> None:
        prestation_id = self._selected_prestation_id()

        if prestation_id is None:
            QMessageBox.information(self, "IntermiPaie", "Sélectionnez une prestation.")
            return

        prestation = self.service.get_prestation(prestation_id)

        if prestation is None:
            QMessageBox.warning(self, "IntermiPaie", "Cette prestation n'existe plus.")
            self.refresh_table()
            return

        dialog = IntermiPaieDialog(
            self,
            prestation=prestation,
            artist_service=self.artist_service,
            organization_service=self.organization_service,
            contract_service=self.contract_service,
            devis_service=self.devis_service,
            facture_service=self.facture_service,
        )
        dialog.exec()

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
                if column == self.DATE_COLUMN:
                    item = DateTableWidgetItem(value)
                else:
                    item = self._make_item(value)
                self.table.setItem(row, column, item)

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
        self.btn_create_devis.setEnabled(has_selection)
        self.btn_create_facture.setEnabled(has_selection)
        self.btn_create_cddu.setEnabled(has_selection)
        self.btn_intermipaie.setEnabled(has_selection)
