from __future__ import annotations

from typing import Any

from PySide6.QtCore import QDate, QSettings
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models.prestation import Prestation
from app.services.artist_service import ArtistService
from app.services.organization_service import OrganizationService
from app.services.prestation_service import PrestationService

DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 850

TYPES_EVENEMENT = (
    ("Mariage", "mariage"),
    ("Festival", "festival"),
    ("Mairie", "mairie"),
    ("Comite d'entreprise", "comite_entreprise"),
    ("Anniversaire", "anniversaire"),
    ("Soiree privee", "soiree_privee"),
    ("Autre", "autre"),
)


class PrestationDialog(QDialog):
    def __init__(
        self,
        parent: Any = None,
        prestation: Prestation | None = None,
        service: PrestationService | None = None,
        artist_service: ArtistService | None = None,
        organization_service: OrganizationService | None = None,
    ) -> None:
        super().__init__(parent)

        self.service = service or PrestationService()
        self.artist_service = artist_service or ArtistService()
        self.organization_service = organization_service or OrganizationService()
        self._source_prestation = prestation
        self.prestation = prestation or Prestation(reference=self.service.next_reference())

        self.setWindowTitle("Modifier une prestation" if prestation else "Nouvelle prestation")
        self.setMinimumSize(900, 600)

        self._settings = QSettings("YGNTManager", "PrestationDialog")
        saved_geometry = self._settings.value("geometry")
        if saved_geometry is not None:
            self.restoreGeometry(saved_geometry)
        else:
            self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self._build_general_tab()
        self._build_artist_tab()
        self._build_organizer_tab()
        self._build_location_tab()
        self._build_notes_tab()

        # Les boutons restent en dehors des onglets : toujours visibles, jamais coupes.
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setText("Enregistrer")
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        self.buttons.accepted.connect(self.save)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self._fill_form(self.prestation)

        # Connectes apres le remplissage initial : un changement manuel de
        # l'utilisateur declenche l'auto-remplissage, pas le chargement du formulaire.
        self.artist_combo.currentIndexChanged.connect(self._on_artist_selected)
        self.organization_combo.currentIndexChanged.connect(self._on_organization_selected)

        # La taille du dialogue est memorisee, quelle que soit la maniere dont il se ferme.
        self.finished.connect(self._save_geometry)

    @staticmethod
    def _wrap_in_scroll(content: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(content)
        return scroll

    # ===== Construction des onglets =====

    def _build_general_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.reference = QLineEdit()
        self.reference.setReadOnly(True)

        self.type_evenement = QComboBox()
        for label, value in TYPES_EVENEMENT:
            self.type_evenement.addItem(label, value)

        self.nom = QLineEdit()

        self.statut = QComboBox()
        for value, label in self.service.STATUSES.items():
            self.statut.addItem(label, value)

        self.date_debut = QDateEdit()
        self.date_debut.setCalendarPopup(True)
        self.date_debut.setDate(QDate.currentDate())

        self.date_fin = QDateEdit()
        self.date_fin.setCalendarPopup(True)
        self.date_fin.setDate(QDate.currentDate())

        form.addRow("Reference", self.reference)
        form.addRow("Type d'evenement", self.type_evenement)
        form.addRow("Nom", self.nom)
        form.addRow("Statut", self.statut)
        form.addRow("Date de debut", self.date_debut)
        form.addRow("Date de fin", self.date_fin)

        self.tabs.addTab(self._wrap_in_scroll(content), "General")

    def _build_artist_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.artist_combo = QComboBox()
        self._reload_artist_choices()

        self.artiste_nom = QLineEdit()
        self.artiste_nom.setReadOnly(True)
        self.artiste_adresse = QLineEdit()
        self.artiste_adresse.setReadOnly(True)
        self.artiste_city = QLineEdit()
        self.artiste_city.setReadOnly(True)
        self.artiste_phone = QLineEdit()
        self.artiste_phone.setReadOnly(True)
        self.artiste_email = QLineEdit()
        self.artiste_email.setReadOnly(True)
        self.artiste_siret = QLineEdit()
        self.artiste_siret.setReadOnly(True)
        self.artiste_fee = QLineEdit()
        self.artiste_fee.setReadOnly(True)

        form.addRow("Artiste", self.artist_combo)
        form.addRow("Nom", self.artiste_nom)
        form.addRow("Adresse", self.artiste_adresse)
        form.addRow("Ville", self.artiste_city)
        form.addRow("Telephone", self.artiste_phone)
        form.addRow("Email", self.artiste_email)
        form.addRow("SIRET", self.artiste_siret)
        form.addRow("Cachet habituel", self.artiste_fee)

        self.tabs.addTab(self._wrap_in_scroll(content), "Artiste")

    def _build_organizer_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.organization_combo = QComboBox()
        self._reload_organization_choices()

        self.organisateur_nom = QLineEdit()
        self.organisateur_nom.setReadOnly(True)
        self.organisateur_adresse = QLineEdit()
        self.organisateur_adresse.setReadOnly(True)
        self.organisateur_city = QLineEdit()
        self.organisateur_city.setReadOnly(True)
        self.organisateur_phone = QLineEdit()
        self.organisateur_phone.setReadOnly(True)
        self.organisateur_email = QLineEdit()
        self.organisateur_email.setReadOnly(True)
        self.organisateur_siret = QLineEdit()
        self.organisateur_siret.setReadOnly(True)

        form.addRow("Organisateur", self.organization_combo)
        form.addRow("Nom", self.organisateur_nom)
        form.addRow("Adresse", self.organisateur_adresse)
        form.addRow("Ville", self.organisateur_city)
        form.addRow("Telephone", self.organisateur_phone)
        form.addRow("Email", self.organisateur_email)
        form.addRow("SIRET", self.organisateur_siret)

        self.tabs.addTab(self._wrap_in_scroll(content), "Organisateur")

    def _build_location_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.lieu_nom = QLineEdit()
        self.lieu_adresse = QLineEdit()
        self.lieu_postal_code = QLineEdit()
        self.lieu_city = QLineEdit()

        form.addRow("Lieu (nom de la salle)", self.lieu_nom)
        form.addRow("Adresse", self.lieu_adresse)
        form.addRow("Code postal", self.lieu_postal_code)
        form.addRow("Ville", self.lieu_city)

        self.tabs.addTab(self._wrap_in_scroll(content), "Lieu")

    def _build_notes_tab(self) -> None:
        content = QWidget()
        layout = QVBoxLayout(content)

        self.notes = QTextEdit()
        layout.addWidget(self.notes)

        self.tabs.addTab(content, "Notes")

    # ===== Listes deroulantes Artiste / Organisateur =====

    def _reload_artist_choices(self) -> None:
        self.artist_combo.addItem("(Aucun)", None)
        for artist in self.artist_service.list_artists():
            label = artist.stage_name or artist.legal_name or f"Artiste #{artist.id}"
            self.artist_combo.addItem(label, artist.id)

    def _reload_organization_choices(self) -> None:
        self.organization_combo.addItem("(Aucun)", None)
        for organization in self.organization_service.list_organizations():
            label = organization.name or f"Organisateur #{organization.id}"
            self.organization_combo.addItem(label, organization.id)

    def _on_artist_selected(self, _index: int) -> None:
        artist_id = self.artist_combo.currentData()

        if artist_id is None:
            self._clear_artist_fields()
            return

        artist = self.artist_service.get_artist(artist_id)
        if artist is None:
            self._clear_artist_fields()
            return

        self.artiste_nom.setText(artist.stage_name or artist.legal_name or "")
        self.artiste_adresse.setText(artist.address or "")
        self.artiste_city.setText(artist.city or "")
        self.artiste_phone.setText(artist.phone or "")
        self.artiste_email.setText(artist.email or "")
        self.artiste_siret.setText(artist.siret or "")
        self.artiste_fee.setText(f"{float(artist.fee or 0):.2f} EUR")

    def _clear_artist_fields(self) -> None:
        for field in (
            self.artiste_nom,
            self.artiste_adresse,
            self.artiste_city,
            self.artiste_phone,
            self.artiste_email,
            self.artiste_siret,
            self.artiste_fee,
        ):
            field.setText("")

    def _on_organization_selected(self, _index: int) -> None:
        organization_id = self.organization_combo.currentData()

        if organization_id is None:
            self._clear_organization_fields()
            return

        organization = self.organization_service.get_organization(organization_id)
        if organization is None:
            self._clear_organization_fields()
            return

        self.organisateur_nom.setText(organization.name or "")
        self.organisateur_adresse.setText(organization.address or "")
        self.organisateur_city.setText(organization.city or "")
        self.organisateur_phone.setText(organization.phone or "")
        self.organisateur_email.setText(organization.email or "")
        self.organisateur_siret.setText(organization.siret or "")

    def _clear_organization_fields(self) -> None:
        for field in (
            self.organisateur_nom,
            self.organisateur_adresse,
            self.organisateur_city,
            self.organisateur_phone,
            self.organisateur_email,
            self.organisateur_siret,
        ):
            field.setText("")

    def _save_geometry(self) -> None:
        self._settings.setValue("geometry", self.saveGeometry())

    # ===== Sauvegarde =====

    def save(self) -> None:
        try:
            prestation = self._build_prestation()
        except ValueError as exc:
            QMessageBox.warning(self, "Prestation incomplete", str(exc))
            return

        self.prestation = prestation
        self.accept()

    def _build_prestation(self) -> Prestation:
        prestation = Prestation(
            id=self._source_prestation.id if self._source_prestation else None,
            reference=self.reference.text().strip(),
            type_evenement=str(self.type_evenement.currentData() or ""),
            nom=self.nom.text().strip(),
            statut=str(self.statut.currentData() or "prospection"),
            date_debut=self.date_debut.date().toString("dd/MM/yyyy"),
            date_fin=self.date_fin.date().toString("dd/MM/yyyy"),
            artist_id=self.artist_combo.currentData(),
            organization_id=self.organization_combo.currentData(),
            lieu_nom=self.lieu_nom.text().strip(),
            lieu_adresse=self.lieu_adresse.text().strip(),
            lieu_postal_code=self.lieu_postal_code.text().strip(),
            lieu_city=self.lieu_city.text().strip(),
            notes=self.notes.toPlainText().strip(),
            created_at=self._source_prestation.created_at if self._source_prestation else None,
            updated_at=self._source_prestation.updated_at if self._source_prestation else None,
        )

        if not prestation.nom.strip():
            raise ValueError("Le nom de la prestation est obligatoire.")
        if not prestation.date_debut.strip():
            raise ValueError("La date de la prestation est obligatoire.")

        return prestation

    def _fill_form(self, prestation: Prestation) -> None:
        self.reference.setText(prestation.reference or self.service.next_reference())

        type_index = self.type_evenement.findData(prestation.type_evenement or "autre")
        self.type_evenement.setCurrentIndex(type_index if type_index >= 0 else 0)

        self.nom.setText(prestation.nom or "")

        statut_index = self.statut.findData(prestation.statut or "prospection")
        self.statut.setCurrentIndex(statut_index if statut_index >= 0 else 0)

        date_debut = QDate.fromString(prestation.date_debut, "dd/MM/yyyy")
        if date_debut.isValid():
            self.date_debut.setDate(date_debut)

        date_fin = QDate.fromString(prestation.date_fin, "dd/MM/yyyy")
        self.date_fin.setDate(date_fin if date_fin.isValid() else self.date_debut.date())

        artist_index = self.artist_combo.findData(prestation.artist_id)
        self.artist_combo.setCurrentIndex(artist_index if artist_index >= 0 else 0)

        organization_index = self.organization_combo.findData(prestation.organization_id)
        self.organization_combo.setCurrentIndex(organization_index if organization_index >= 0 else 0)

        self.lieu_nom.setText(prestation.lieu_nom or "")
        self.lieu_adresse.setText(prestation.lieu_adresse or "")
        self.lieu_postal_code.setText(prestation.lieu_postal_code or "")
        self.lieu_city.setText(prestation.lieu_city or "")

        self.notes.setPlainText(prestation.notes or "")

        # Pre-remplissage initial si un artiste/organisateur est deja lie.
        self._on_artist_selected(self.artist_combo.currentIndex())
        self._on_organization_selected(self.organization_combo.currentIndex())
