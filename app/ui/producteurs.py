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

from app.models.producteur import Producteur
from app.services.producteur_service import ProducteurService
from app.ui.dialogs import confirm_delete
from app.ui.producteur_dialog import ProducteurDialog
from app.ui.theme import mark_destructive, style_page_title, style_table


class ProducteursPage(QWidget):
    HEADERS = (
        "ID",
        "Nom",
        "Forme juridique",
        "SIRET",
        "Ville",
        "Telephone",
        "Email",
        "Actif",
    )

    def __init__(self, service: ProducteurService | None = None) -> None:
        super().__init__()

        self.service = service or ProducteurService()
        self._producteurs: list[Producteur] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Producteurs")
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
        self.table.itemDoubleClicked.connect(self.edit_selected_producteur)
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
        self.btn_set_active = QPushButton("Definir comme actif")
        self.btn_refresh = QPushButton("Actualiser")

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher un producteur...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh_table)

        self.btn_add.clicked.connect(self.new_producteur)
        self.btn_edit.clicked.connect(self.edit_selected_producteur)
        self.btn_delete.clicked.connect(self.delete_selected_producteur)
        self.btn_set_active.clicked.connect(self.activate_selected_producteur)
        self.btn_refresh.clicked.connect(self.refresh_table)

        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_delete)
        toolbar.addWidget(self.btn_set_active)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        toolbar.addWidget(self.search, 1)

        return toolbar

    def new_producteur(self) -> None:
        dialog = ProducteurDialog(self)

        if dialog.exec() and dialog.producteur is not None:
            try:
                self.service.create_producteur(dialog.producteur)
            except ValueError as exc:
                QMessageBox.warning(self, "Producteur invalide", str(exc))
                return

            self.refresh_table()

    def edit_selected_producteur(self, *_args: Any) -> None:
        producteur_id = self._selected_producteur_id()

        if producteur_id is None:
            QMessageBox.information(self, "Modification", "Selectionnez un producteur.")
            return

        producteur = self.service.get_producteur(producteur_id)

        if producteur is None:
            QMessageBox.warning(self, "Modification", "Ce producteur n'existe plus.")
            self.refresh_table()
            return

        dialog = ProducteurDialog(self, producteur)

        if dialog.exec() and dialog.producteur is not None:
            try:
                self.service.update_producteur(dialog.producteur)
            except ValueError as exc:
                QMessageBox.warning(self, "Producteur invalide", str(exc))
                return

            self.refresh_table()

    def delete_selected_producteur(self) -> None:
        producteur_id = self._selected_producteur_id()

        if producteur_id is None:
            QMessageBox.information(self, "Suppression", "Selectionnez un producteur.")
            return

        producteur = self.service.get_producteur(producteur_id)
        label = producteur.nom if producteur and producteur.nom else "ce producteur"

        if confirm_delete(self, label):
            self.service.delete_producteur(producteur_id)
            self.refresh_table()

    def activate_selected_producteur(self) -> None:
        producteur_id = self._selected_producteur_id()

        if producteur_id is None:
            QMessageBox.information(self, "Producteur actif", "Selectionnez un producteur.")
            return

        try:
            self.service.set_active(producteur_id)
        except ValueError as exc:
            QMessageBox.warning(self, "Producteur actif", str(exc))
            return

        self.refresh_table()

    def refresh_table(self) -> None:
        self._producteurs = self.service.search_producteurs(self.search.text())
        self._fill_table(self._producteurs)
        self._sync_buttons()

    def _fill_table(self, producteurs: list[Producteur]) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(producteurs))

        for row, producteur in enumerate(producteurs):
            values = (
                producteur.id,
                producteur.nom,
                producteur.forme_juridique,
                producteur.siret,
                producteur.city,
                producteur.phone,
                producteur.email,
                "Oui" if producteur.actif else "Non",
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

    def _selected_producteur_id(self) -> int | None:
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
        has_selection = self._selected_producteur_id() is not None
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)
        self.btn_set_active.setEnabled(has_selection)
