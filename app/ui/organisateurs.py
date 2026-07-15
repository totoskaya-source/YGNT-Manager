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

from app.models.organization import Organization
from app.services.organization_service import OrganizationService
from app.ui.dialogs import confirm_delete
from app.ui.organization_dialog import OrganizationDialog
from app.ui.theme import mark_destructive, style_page_title, style_table


class OrganisateursPage(QWidget):
    HEADERS = (
        "ID",
        "Nom",
        "Forme juridique",
        "SIRET",
        "Ville",
        "Téléphone",
        "Email",
        "President",
    )

    def __init__(self, service: OrganizationService | None = None) -> None:
        super().__init__()

        self.service = service or OrganizationService()
        self._organizations: list[Organization] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Organisateurs")
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
        self.table.itemDoubleClicked.connect(self.edit_selected_organization)
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
        self.search.setPlaceholderText("Rechercher un organisateur...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh_table)

        self.btn_add.clicked.connect(self.new_organization)
        self.btn_edit.clicked.connect(self.edit_selected_organization)
        self.btn_delete.clicked.connect(self.delete_selected_organization)
        self.btn_refresh.clicked.connect(self.refresh_table)

        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_delete)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        toolbar.addWidget(self.search, 1)

        return toolbar

    def new_organization(self) -> None:
        dialog = OrganizationDialog(self)

        if dialog.exec() and dialog.organization is not None:
            try:
                self.service.create_organization(dialog.organization)
            except ValueError as exc:
                QMessageBox.warning(self, "Organisateur invalide", str(exc))
                return

            self.refresh_table()

    def edit_selected_organization(self, *_args: Any) -> None:
        organization_id = self._selected_organization_id()

        if organization_id is None:
            QMessageBox.information(self, "Modification", "Sélectionnez un organisateur.")
            return

        organization = self.service.get_organization(organization_id)

        if organization is None:
            QMessageBox.warning(self, "Modification", "Cet organisateur n'existe plus.")
            self.refresh_table()
            return

        dialog = OrganizationDialog(self, organization)

        if dialog.exec() and dialog.organization is not None:
            try:
                self.service.update_organization(dialog.organization)
            except ValueError as exc:
                QMessageBox.warning(self, "Organisateur invalide", str(exc))
                return

            self.refresh_table()

    def delete_selected_organization(self) -> None:
        organization_id = self._selected_organization_id()

        if organization_id is None:
            QMessageBox.information(self, "Suppression", "Sélectionnez un organisateur.")
            return

        organization = self.service.get_organization(organization_id)
        label = self._organization_label(organization) if organization else "cet organisateur"

        if confirm_delete(self, label):
            self.service.delete_organization(organization_id)
            self.refresh_table()

    def refresh_table(self) -> None:
        self._organizations = self.service.search_organizations(self.search.text())
        self._fill_table(self._organizations)
        self._sync_buttons()

    def _fill_table(self, organizations: list[Organization]) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(organizations))

        for row, organization in enumerate(organizations):
            values = (
                organization.id,
                organization.name,
                organization.legal_form,
                organization.siret,
                organization.city,
                organization.phone,
                organization.email,
                organization.president,
            )

            for column, value in enumerate(values):
                item = self._make_item(value)
                self.table.setItem(row, column, item)

        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def _make_item(self, value: Any) -> QTableWidgetItem:
        item = QTableWidgetItem("" if value is None else str(value))
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        return item

    def _selected_organization_id(self) -> int | None:
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
        has_selection = self._selected_organization_id() is not None
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)

    def _organization_label(self, organization: Organization | None) -> str:
        if organization is None:
            return "cet organisateur"

        return organization.name or "cet organisateur"
