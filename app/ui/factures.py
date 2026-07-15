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

from app.models.facture import Facture
from app.services.facture_service import FactureService
from app.services.paiement_service import PaiementService
from app.ui.dialogs import confirm_delete, notify_success
from app.ui.facture_dialog import FactureDialog
from app.ui.paiement_dialog import PaiementDialog
from app.ui.theme import DateTableWidgetItem, mark_destructive, style_page_title, style_table


class FacturesPage(QWidget):
    HEADERS = (
        "ID",
        "Référence",
        "Date",
        "Formation",
        "Organisateur",
        "Objet",
        "Montant",
        "Statut",
    )
    # Index de la colonne Date : trie chronologiquement via
    # DateTableWidgetItem plutot que comme du texte (v1.0.3, BUG-001).
    DATE_COLUMN = 2

    def __init__(
        self,
        service: FactureService | None = None,
        paiement_service: PaiementService | None = None,
    ) -> None:
        super().__init__()

        self.service = service or FactureService()
        self.paiement_service = paiement_service or PaiementService(facture_service=self.service)
        self._factures: list[Facture] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Factures")
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
        self.table.itemDoubleClicked.connect(self.edit_selected_facture)
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
        self.btn_create_paiement = QPushButton("💳 Créer un paiement")
        self.btn_refresh = QPushButton("Actualiser")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher une facture...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh_table)

        self.btn_add.clicked.connect(self.new_facture)
        self.btn_edit.clicked.connect(self.edit_selected_facture)
        self.btn_delete.clicked.connect(self.delete_selected_facture)
        self.btn_create_paiement.clicked.connect(self.create_paiement_from_selected_facture)
        self.btn_refresh.clicked.connect(self.refresh_table)

        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_delete)
        toolbar.addWidget(self.btn_create_paiement)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        toolbar.addWidget(self.search, 1)

        return toolbar

    def new_facture(self) -> None:
        # Le dialogue s'enregistre desormais lui-meme (Sprint 12.0) : il reste
        # ouvert apres la creation pour generer immediatement DOCX/PDF, sans
        # repasser par cette liste. On se contente de rafraichir au retour.
        dialog = FactureDialog(self, service=self.service)
        dialog.exec()
        self.refresh_table()

    def edit_selected_facture(self, *_args: Any) -> None:
        facture_id = self._selected_facture_id()

        if facture_id is None:
            QMessageBox.information(self, "Modification", "Sélectionnez une facture.")
            return

        facture = self.service.get_facture(facture_id)

        if facture is None:
            QMessageBox.warning(self, "Modification", "Cette facture n'existe plus.")
            self.refresh_table()
            return

        dialog = FactureDialog(self, facture=facture, service=self.service)
        dialog.exec()
        self.refresh_table()

    def delete_selected_facture(self) -> None:
        facture_id = self._selected_facture_id()

        if facture_id is None:
            QMessageBox.information(self, "Suppression", "Sélectionnez une facture.")
            return

        facture = self.service.get_facture(facture_id)
        label = facture.facture_number if facture and facture.facture_number else "cette facture"

        if confirm_delete(self, label):
            self.service.delete_facture(facture_id)
            self.refresh_table()

    def create_paiement_from_selected_facture(self) -> None:
        facture = self._selected_facture()

        if facture is None or facture.id is None:
            QMessageBox.information(self, "Créer un paiement", "Sélectionnez une facture.")
            return

        # La facture n'est jamais modifiee ici : le paiement est un nouveau
        # document independant, pre-rempli puis toujours modifiable avant
        # enregistrement (meme principe que Devis/Contrat/Facture depuis une
        # autre entite). Le statut de la facture ne sera mis a jour qu'apres
        # l'enregistrement reel du paiement, via PaiementService.
        seed = self.paiement_service.build_from_facture(facture)

        dialog = PaiementDialog(
            self,
            initial_paiement=seed,
            service=self.paiement_service,
            facture_service=self.service,
        )

        if dialog.exec():
            try:
                self.paiement_service.create_paiement(dialog.paiement)
            except ValueError as exc:
                QMessageBox.warning(self, "Paiement invalide", str(exc))
                return

            notify_success(self, "Paiement enregistré.")
            self.refresh_table()

    def refresh_table(self) -> None:
        self._factures = self.service.search_factures(self.search.text())
        self._fill_table(self._factures)
        self._sync_buttons()

    def _fill_table(self, factures: list[Facture]) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(factures))

        for row, facture in enumerate(factures):
            values = (
                facture.id,
                facture.facture_number,
                facture.prestation_date,
                facture.formation_nom,
                facture.organisateur_structure,
                facture.spectacle_nom,
                float(facture.montant or 0),
                facture.status_label,
            )

            for column, value in enumerate(values):
                if column == self.DATE_COLUMN:
                    item = DateTableWidgetItem(value)
                else:
                    item = self._make_item(value)
                if column == 6:
                    # L'ordre importe : EditRole doit etre fixe avant le texte
                    # affiche, sinon Qt reaffiche la valeur brute (voir Devis).
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

    def _selected_facture_id(self) -> int | None:
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

    def _selected_facture(self) -> Facture | None:
        facture_id = self._selected_facture_id()
        return self.service.get_facture(facture_id) if facture_id is not None else None

    def _sync_buttons(self) -> None:
        has_selection = self._selected_facture_id() is not None
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)
        self.btn_create_paiement.setEnabled(has_selection)
