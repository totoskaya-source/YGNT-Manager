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

from app.models.artist import Artist
from app.services.artist_service import ArtistService
from app.ui.artist_dialog import ArtistDialog
from app.ui.dialogs import confirm_delete
from app.ui.theme import mark_destructive, style_page_title, style_table


class ArtistesPage(QWidget):
    HEADERS = (
        "ID",
        "Nom",
        "Prénom",
        "Nom de scène",
        "Instrument principal",
        "Statut",
    )

    def __init__(self, service: ArtistService | None = None) -> None:
        super().__init__()

        self.service = service or ArtistService()
        self._artists: list[Artist] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        title = QLabel("Artistes")
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
        self.table.itemDoubleClicked.connect(self.edit_selected_artist)
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
        self.search.setPlaceholderText("Rechercher un artiste...")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.refresh_table)

        self.btn_add.clicked.connect(self.new_artist)
        self.btn_edit.clicked.connect(self.edit_selected_artist)
        self.btn_delete.clicked.connect(self.delete_selected_artist)
        self.btn_refresh.clicked.connect(self.refresh_table)

        toolbar.addWidget(self.btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_delete)
        toolbar.addWidget(self.btn_refresh)
        toolbar.addStretch()
        toolbar.addWidget(self.search, 1)

        return toolbar

    def new_artist(self) -> None:
        dialog = ArtistDialog(self)

        if dialog.exec() and dialog.artist is not None:
            try:
                self.service.create_artist(dialog.artist)
            except ValueError as exc:
                QMessageBox.warning(self, "Artiste invalide", str(exc))
                return

            self.refresh_table()

    def edit_selected_artist(self, *_args: Any) -> None:
        artist_id = self._selected_artist_id()

        if artist_id is None:
            QMessageBox.information(self, "Modification", "Sélectionnez un artiste.")
            return

        artist = self.service.get_artist(artist_id)

        if artist is None:
            QMessageBox.warning(self, "Modification", "Cet artiste n'existe plus.")
            self.refresh_table()
            return

        dialog = ArtistDialog(self, artist)

        if dialog.exec() and dialog.artist is not None:
            try:
                self.service.update_artist(dialog.artist)
            except ValueError as exc:
                QMessageBox.warning(self, "Artiste invalide", str(exc))
                return

            self.refresh_table()

    def delete_selected_artist(self) -> None:
        artist_id = self._selected_artist_id()

        if artist_id is None:
            QMessageBox.information(self, "Suppression", "Sélectionnez un artiste.")
            return

        artist = self.service.get_artist(artist_id)
        label = self._artist_label(artist) if artist else "cet artiste"

        if confirm_delete(self, label):
            self.service.delete_artist(artist_id)
            self.refresh_table()

    def refresh_table(self) -> None:
        self._artists = self.service.search_artists(self.search.text())
        self._fill_table(self._artists)
        self._sync_buttons()

    def _fill_table(self, artists: list[Artist]) -> None:
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(artists))

        for row, artist in enumerate(artists):
            values = (
                artist.id,
                artist.legal_name,
                artist.first_name,
                artist.stage_name,
                artist.instrument,
                artist.status,
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

    def _selected_artist_id(self) -> int | None:
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
        has_selection = self._selected_artist_id() is not None
        self.btn_edit.setEnabled(has_selection)
        self.btn_delete.setEnabled(has_selection)

    def _artist_label(self, artist: Artist | None) -> str:
        if artist is None:
            return "cet artiste"

        return artist.stage_name or artist.legal_name or "cet artiste"
