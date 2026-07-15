from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models.formation import Formation
from app.services.artist_service import ArtistService
from app.services.formation_artiste_service import FormationArtisteService
from app.services.formation_service import FormationService
from app.ui.dialogs import confirm_delete, notify_success
from app.ui.theme import required_label

DEFAULT_WIDTH = 900
DEFAULT_HEIGHT = 700


class FormationDialog(QDialog):
    """Dialogue de creation/modification d'une Formation (groupe) -
    Sprint 18.0. Une Formation ne represente jamais une personne : sa
    composition (onglet 2) est constituee exclusivement de fiches Artiste
    existantes, via la table de liaison formation_artistes. Meme ergonomie
    que les autres dialogues (QTabWidget, QScrollArea, geometrie memorisee)."""

    def __init__(
        self,
        parent: Any = None,
        formation: Formation | None = None,
        service: FormationService | None = None,
        composition_service: FormationArtisteService | None = None,
        artist_service: ArtistService | None = None,
    ) -> None:
        super().__init__(parent)

        self.service = service or FormationService()
        self.composition_service = composition_service or FormationArtisteService()
        self.artist_service = artist_service or ArtistService()

        self._source_formation = formation
        self.formation = formation

        self.setWindowTitle("Modifier une formation" if formation else "Nouvelle formation")
        self.setMinimumSize(700, 550)

        self._settings = QSettings("YGNTManager", "FormationDialog")
        saved_geometry = self._settings.value("geometry")
        if saved_geometry is not None:
            self.restoreGeometry(saved_geometry)
        else:
            self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self._build_general_tab()
        self._build_composition_tab()

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setText("Enregistrer")
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        self.buttons.accepted.connect(self.save)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        if formation is not None:
            self._fill_form(formation)

        self._reload_artist_choices()
        self._sync_composition_enabled()
        self._refresh_composition_table()
        self._update_close_button()

        self.finished.connect(self._save_geometry)

    @staticmethod
    def _wrap_in_scroll(content: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(content)
        return scroll

    # ===== Onglet General =====

    def _build_general_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.nom = QLineEdit()
        self.style = QLineEdit()

        self.description = QTextEdit()
        self.description.setFixedHeight(100)

        self.logo_path = QLineEdit()
        self.photo_path = QLineEdit()

        form.addRow(required_label("Nom"), self.nom)
        form.addRow("Style", self.style)
        form.addRow("Description", self.description)
        form.addRow("Logo (chemin du fichier)", self.logo_path)
        form.addRow("Photo (chemin du fichier)", self.photo_path)

        self.tabs.addTab(self._wrap_in_scroll(content), "Général")

    # ===== Onglet Composition =====

    def _build_composition_tab(self) -> None:
        content = QWidget()
        layout = QVBoxLayout(content)

        self.composition_hint = QLabel(
            "Enregistrez d'abord la formation (onglet Général) pour gérer sa composition."
        )
        self.composition_hint.setWordWrap(True)
        layout.addWidget(self.composition_hint)

        add_row = QHBoxLayout()
        self.member_combo = QComboBox()
        add_row.addWidget(self.member_combo, 1)
        self.member_role = QLineEdit()
        self.member_role.setPlaceholderText("Rôle (optionnel)")
        add_row.addWidget(self.member_role)
        self.btn_add_member = QPushButton("Ajouter un artiste")
        self.btn_add_member.clicked.connect(self.add_member)
        add_row.addWidget(self.btn_add_member)
        layout.addLayout(add_row)

        self.composition_table = QTableWidget()
        self.composition_table.setColumnCount(4)
        self.composition_table.setHorizontalHeaderLabels(("ID", "Artiste", "Rôle", "Ordre"))
        self.composition_table.setColumnHidden(0, True)
        self.composition_table.setAlternatingRowColors(True)
        self.composition_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.composition_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.composition_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.composition_table.itemSelectionChanged.connect(self._sync_composition_buttons)
        header = self.composition_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(True)
        layout.addWidget(self.composition_table, 1)

        actions = QHBoxLayout()
        self.btn_remove_member = QPushButton("Supprimer")
        self.btn_move_up = QPushButton("Monter")
        self.btn_move_down = QPushButton("Descendre")
        self.btn_edit_role = QPushButton("Modifier le rôle")

        self.btn_remove_member.clicked.connect(self.remove_selected_member)
        self.btn_move_up.clicked.connect(self.move_selected_up)
        self.btn_move_down.clicked.connect(self.move_selected_down)
        self.btn_edit_role.clicked.connect(self.edit_selected_role)

        for button in (self.btn_remove_member, self.btn_move_up, self.btn_move_down, self.btn_edit_role):
            actions.addWidget(button)
        actions.addStretch()
        layout.addLayout(actions)

        self.tabs.addTab(content, "Composition")

    def _reload_artist_choices(self) -> None:
        self.member_combo.clear()
        for artist in self.artist_service.list_artists():
            label = artist.stage_name or artist.legal_name or f"Artiste #{artist.id}"
            self.member_combo.addItem(label, artist.id)

    def _sync_composition_enabled(self) -> None:
        has_id = bool(self._source_formation and self._source_formation.id is not None)
        self.composition_hint.setVisible(not has_id)
        for widget in (self.member_combo, self.member_role, self.btn_add_member, self.composition_table):
            widget.setEnabled(has_id)
        self._sync_composition_buttons()

    def _sync_composition_buttons(self) -> None:
        has_id = bool(self._source_formation and self._source_formation.id is not None)
        has_selection = has_id and self.composition_table.currentRow() >= 0
        for button in (self.btn_remove_member, self.btn_move_up, self.btn_move_down, self.btn_edit_role):
            button.setEnabled(has_selection)

    def _refresh_composition_table(self) -> None:
        if self._source_formation is None or self._source_formation.id is None:
            self.composition_table.setRowCount(0)
            return

        members = self.composition_service.list_composition(self._source_formation.id)
        self.composition_table.setRowCount(len(members))

        for row, member in enumerate(members):
            artist = self.artist_service.get_artist(member.artiste_id)
            label = (artist.stage_name or artist.legal_name) if artist else f"Artiste #{member.artiste_id}"

            for column, value in enumerate((member.id, label, member.role, member.ordre)):
                item = QTableWidgetItem("" if value is None else str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.composition_table.setItem(row, column, item)

        self.composition_table.resizeColumnsToContents()
        self.composition_table.horizontalHeader().setStretchLastSection(True)
        self._sync_composition_buttons()

    def _selected_member_id(self) -> int | None:
        row = self.composition_table.currentRow()
        if row < 0:
            return None
        item = self.composition_table.item(row, 0)
        if item is None:
            return None
        try:
            return int(item.text())
        except ValueError:
            return None

    def add_member(self) -> None:
        if self._source_formation is None or self._source_formation.id is None:
            return

        artiste_id = self.member_combo.currentData()
        if artiste_id is None:
            return

        try:
            self.composition_service.add_member(
                self._source_formation.id,
                artiste_id,
                role=self.member_role.text(),
            )
        except ValueError as exc:
            QMessageBox.warning(self, "Composition", str(exc))
            return

        self.member_role.clear()
        self._refresh_composition_table()

    def remove_selected_member(self) -> None:
        member_id = self._selected_member_id()
        if member_id is None:
            return

        if confirm_delete(self, "ce membre de la formation"):
            self.composition_service.remove_member(member_id)
            self._refresh_composition_table()

    def move_selected_up(self) -> None:
        member_id = self._selected_member_id()
        if member_id is None:
            return
        self.composition_service.move_up(member_id)
        self._refresh_composition_table()

    def move_selected_down(self) -> None:
        member_id = self._selected_member_id()
        if member_id is None:
            return
        self.composition_service.move_down(member_id)
        self._refresh_composition_table()

    def edit_selected_role(self) -> None:
        member_id = self._selected_member_id()
        if member_id is None:
            return

        row = self.composition_table.currentRow()
        current_role = self.composition_table.item(row, 2).text() if row >= 0 else ""

        role, ok = QInputDialog.getText(self, "Modifier le rôle", "Rôle :", text=current_role)
        if not ok:
            return

        self.composition_service.update_role(member_id, role)
        self._refresh_composition_table()

    # ===== Sauvegarde =====

    def _save_geometry(self) -> None:
        self._settings.setValue("geometry", self.saveGeometry())

    def _update_close_button(self) -> None:
        has_saved = bool(self._source_formation and self._source_formation.id is not None)
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(
            "Fermer" if has_saved else "Annuler"
        )

    def save(self) -> None:
        try:
            formation = self._build_formation()
        except ValueError as exc:
            QMessageBox.warning(self, "Formation invalide", str(exc))
            return

        is_new = formation.id is None

        try:
            if is_new:
                formation.id = self.service.create_formation(formation)
            else:
                self.service.update_formation(formation)
        except ValueError as exc:
            QMessageBox.warning(self, "Formation invalide", str(exc))
            return

        saved = self.service.get_formation(formation.id)
        if saved is not None:
            formation = saved

        self.formation = formation
        self._source_formation = formation

        self.setWindowTitle("Modifier une formation")
        self._sync_composition_enabled()
        self._refresh_composition_table()
        self._update_close_button()

        notify_success(self, "Formation créée." if is_new else "Formation modifiée.")

    def _build_formation(self) -> Formation:
        if not self.nom.text().strip():
            raise ValueError("Le nom de la formation est obligatoire.")

        return Formation(
            id=self._source_formation.id if self._source_formation else None,
            nom=self.nom.text().strip(),
            style=self.style.text().strip(),
            description=self.description.toPlainText().strip(),
            logo_path=self.logo_path.text().strip(),
            photo_path=self.photo_path.text().strip(),
            created_at=self._source_formation.created_at if self._source_formation else None,
            updated_at=self._source_formation.updated_at if self._source_formation else None,
        )

    def _fill_form(self, formation: Formation) -> None:
        self.nom.setText(formation.nom or "")
        self.style.setText(formation.style or "")
        self.description.setPlainText(formation.description or "")
        self.logo_path.setText(formation.logo_path or "")
        self.photo_path.setText(formation.photo_path or "")
