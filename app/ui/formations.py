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

from app.models.formation import Formation
from app.services.formation_artiste_service import FormationArtisteService
from app.services.formation_service import FormationService
from app.ui.dialogs import confirm_delete
from app.ui.formation_dialog import FormationDialog
from app.ui.theme import mark_destructive, style_page_title, style_table


class FormationsPage(QWidget):
    """Liste des Formations (groupes) - Sprint 18.0. Ecran independant, ne
    reutilise pas ArtistesPage : une Formation n'est jamais une personne."""

    HEADERS = (
        "ID",
        "Nom",
        "Style",
        "Membres",
    )

    def __init__(
        self,
        service: FormationService | None = None,
        composition_service: FormationArtisteService | None = None,
    ) -> None:
        super().__init__()

        self.service = service or FormationService()
        self.composition_service = composition_service or FormationArtisteService()
        self._formations: list[Formation] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Formations")
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
        self.table.itemDoubleClicked.connect(self.edit_selected_formation)
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

        self.btn_new = QPushButton("Nouveau")
        self.btn_edit = QPushButton("Modifier")
        self.btn_delete = QPushButton("Supprimer")
        mark_destructive(self.btn_delete)
        self.btn_refresh = QPushButton("Actualiser")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher une formation...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh_table)

        self.btn_new.clicked.connect(self.new_formation)
        self.btn_edit.clicked.connect(self.edit_selected_formation)
        self.btn_delete.clicked.connect(self.delete_selected_formation)
        self.btn_refresh.clicked.connect(self.refresh_table)

        toolbar.addWidget(self.btn_new)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_delete)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        toolbar.addWidget(self.search, 1)

        return toolbar

    def new_formation(self) -> None:
        dialog = FormationDialog(self, service=self.service, composition_service=self.composition_service)
        dialog.exec()
        self.refresh_table()

    def edit_selected_formation(self, *_args: Any) -> None:
        formation_id = self._selected_formation_id()

        if formation_id is None:
            QMessageBox.information(self, "Modification", "Sélectionnez une formation.")
            return

        formation = self.service.get_formation(formation_id)

        if formation is None:
            QMessageBox.warning(self, "Modification", "Cette formation n'existe plus.")
            self.refresh_table()
            return

        dialog = FormationDialog(
            self,
            formation=formation,
            service=self.service,
            composition_service=self.composition_service,
        )
        dialog.exec()
        self.refresh_table()

    def delete_selected_formation(self) -> None:
        formation_id = self._selected_formation_id()

        if formation_id is None:
            QMessageBox.information(self, "Suppression", "Sélectionnez une formation.")
            return

        formation = self.service.get_formation(formation_id)
        label = formation.nom if formation else "cette formation"

        if confirm_delete(self, label):
            self.service.delete_formation(formation_id)
            self.refresh_table()

    def refresh_table(self) -> None:
        self._formations = self.service.search_formations(self.search.text())
        self._fill_table(self._formations)
        self._sync_buttons()

    def _fill_table(self, formations: list[Formation]) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(formations))

        for row, formation in enumerate(formations):
            member_count = len(self.composition_service.list_composition(formation.id)) if formation.id else 0

            values = (
                formation.id,
                formation.nom,
                formation.style,
                member_count,
            )

            for column, value in enumerate(values):
                self.table.setItem(row, column, self._make_item(value))

        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def _make_item(self, value: Any) -> QTableWidgetItem:
        item = QTableWidgetItem("" if value is None else str(value))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _selected_formation_id(self) -> int | None:
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
        has_selection = self._selected_formation_id() is not None
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)
