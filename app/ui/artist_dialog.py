from __future__ import annotations

from typing import Any

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QComboBox,
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

from app.models.artist import Artist
from app.ui.theme import required_label

DEFAULT_WIDTH = 900
DEFAULT_HEIGHT = 700


class ArtistDialog(QDialog):
    """Dialogue de creation/modification d'un Artiste - Sprint 17.1.

    Reprend exactement l'ergonomie déjà utilisee par ContractDialog,
    CdduDialog, OrganizationDialog et PrestationDialog : dialogue
    redimensionnable, QTabWidget, onglets enveloppes dans un QScrollArea,
    geometrie memorisee via QSettings. Aucune logique metier modifiée :
    meme regle de validation qu'avant (nom ou nom de scène obligatoire),
    seuls l'organisation des champs et les libelles changent."""

    def __init__(self, parent: Any = None, artist: Artist | None = None) -> None:
        super().__init__(parent)

        self._source_artist = artist
        self.artist: Artist | None = None

        self.setWindowTitle("Modifier un artiste" if artist else "Nouvel artiste")
        self.setMinimumSize(700, 550)

        self._settings = QSettings("YGNTManager", "ArtistDialog")
        saved_geometry = self._settings.value("geometry")
        if saved_geometry is not None:
            self.restoreGeometry(saved_geometry)
        else:
            self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self._build_identity_tab()
        self._build_contact_tab()
        self._build_artistic_tab()
        self._build_administrative_tab()

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setText("Enregistrer")
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        self.buttons.accepted.connect(self.save)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        if artist is not None:
            self._fill_form(artist)

        self.finished.connect(self._save_geometry)

    @staticmethod
    def _wrap_in_scroll(content: QWidget) -> QScrollArea:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(content)
        return scroll

    # ===== Construction des onglets =====

    def _build_identity_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.legal_name = QLineEdit()
        self.legal_name.setToolTip("Nom légal ou nom de scène : l'un des deux est obligatoire.")
        self.first_name = QLineEdit()
        self.stage_name = QLineEdit()
        self.stage_name.setPlaceholderText("Optionnel si le nom légal est renseigné")
        self.stage_name.setToolTip("Nom légal ou nom de scène : l'un des deux est obligatoire.")

        self.birth_date = QLineEdit()
        self.birth_date.setPlaceholderText("jj/mm/aaaa")
        self.birth_place = QLineEdit()
        self.social_number = QLineEdit()
        self.conges_spectacle_number = QLineEdit()

        self.status = QComboBox()
        self.status.addItems([
            "Intermittent",
            "Salarié",
            "Auto-entrepreneur",
            "Autre",
        ])

        # Qualification / Fonction (Sprint 18.2) : obligatoire, utilisee
        # telle quelle par le CDDU ("en qualite de ..."), jamais de valeur
        # codee en dur ailleurs dans le code - toujours issue de ce champ.
        # Sprint 20 : plus aucune valeur par defaut - le premier element est
        # un placeholder non valide, l'utilisateur doit choisir activement
        # (voir save() : impossible d'enregistrer tant qu'il reste selectionne).
        self.qualification = QComboBox()
        self.qualification.addItem("— Sélectionnez une qualification —")
        self.qualification.addItems([
            "Artiste musicien",
            "Chanteur",
            "Danseur",
            "Technicien du spectacle",
            "Régisseur",
            "Ingénieur du son",
            "Ingénieur lumière",
            "Road manager",
            "Autre",
        ])

        form.addRow(required_label("Nom"), self.legal_name)
        form.addRow("Prénom", self.first_name)
        form.addRow("Nom de scène", self.stage_name)
        form.addRow("Date de naissance", self.birth_date)
        form.addRow("Lieu de naissance", self.birth_place)
        form.addRow("Numéro de sécurité sociale", self.social_number)
        form.addRow("Numéro de congés spectacle", self.conges_spectacle_number)
        form.addRow("Statut", self.status)
        form.addRow(required_label("Qualification / Fonction"), self.qualification)

        self.tabs.addTab(self._wrap_in_scroll(content), "Identité")

    def _build_contact_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.address = QLineEdit()
        self.postal_code = QLineEdit()
        self.city = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.site_internet = QLineEdit()

        form.addRow("Adresse", self.address)
        form.addRow("Code postal", self.postal_code)
        form.addRow("Ville", self.city)
        form.addRow("Téléphone", self.phone)
        form.addRow("Email", self.email)
        form.addRow("Site internet", self.site_internet)

        self.tabs.addTab(self._wrap_in_scroll(content), "Coordonnées")

    def _build_artistic_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.instrument = QLineEdit()
        self.secondary_instruments = QLineEdit()
        self.secondary_instruments.setPlaceholderText("Ex : Piano, Percussions...")
        self.style_musical = QLineEdit()

        self.description = QTextEdit()
        self.description.setFixedHeight(90)

        self.logo_path = QLineEdit()
        self.photo_path = QLineEdit()

        form.addRow("Instrument principal", self.instrument)
        form.addRow("Instruments secondaires", self.secondary_instruments)
        form.addRow("Style(s) musical(aux)", self.style_musical)
        form.addRow("Biographie / Présentation", self.description)
        form.addRow("Logo (chemin du fichier)", self.logo_path)
        form.addRow("Photo (chemin du fichier)", self.photo_path)

        self.tabs.addTab(self._wrap_in_scroll(content), "Artistique")

    def _build_administrative_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.notes = QTextEdit()
        self.notes.setFixedHeight(100)
        self.comments = QTextEdit()
        self.comments.setFixedHeight(100)

        form.addRow("Notes internes", self.notes)
        form.addRow("Commentaires", self.comments)

        self.tabs.addTab(self._wrap_in_scroll(content), "Administratif")

    # ===== Sauvegarde =====

    def _save_geometry(self) -> None:
        self._settings.setValue("geometry", self.saveGeometry())

    def save(self) -> None:
        if not self.legal_name.text().strip() and not self.stage_name.text().strip():
            QMessageBox.warning(
                self,
                "Artiste incomplet",
                "Renseignez au moins le nom ou le nom de scène.",
            )
            return

        if self.qualification.currentIndex() == 0:
            QMessageBox.warning(
                self,
                "Artiste incomplet",
                "Sélectionnez une qualification.",
            )
            return

        self.artist = Artist(
            id=self._source_artist.id if self._source_artist else None,
            legal_name=self.legal_name.text().strip(),
            first_name=self.first_name.text().strip(),
            stage_name=self.stage_name.text().strip(),
            address=self.address.text().strip(),
            postal_code=self.postal_code.text().strip(),
            city=self.city.text().strip(),
            phone=self.phone.text().strip(),
            email=self.email.text().strip(),
            site_internet=self.site_internet.text().strip(),
            instrument=self.instrument.text().strip(),
            secondary_instruments=self.secondary_instruments.text().strip(),
            status=self.status.currentText(),
            qualification=self.qualification.currentText(),
            # Cachet habituel retire de l'interface (Sprint 8.7) : la valeur
            # deja enregistree est conservee telle quelle, jamais resaisie.
            fee=self._source_artist.fee if self._source_artist else 0.0,
            birth_date=self.birth_date.text().strip(),
            birth_place=self.birth_place.text().strip(),
            social_number=self.social_number.text().strip(),
            conges_spectacle_number=self.conges_spectacle_number.text().strip(),
            # Informations legales/bancaires : pas encore exposees dans ce
            # dialogue (deja absentes de l'ancienne interface), la valeur
            # deja enregistree est conservee telle quelle.
            siren=self._source_artist.siren if self._source_artist else "",
            siret=self._source_artist.siret if self._source_artist else "",
            ape=self._source_artist.ape if self._source_artist else "",
            licence=self._source_artist.licence if self._source_artist else "",
            iban=self._source_artist.iban if self._source_artist else "",
            bic=self._source_artist.bic if self._source_artist else "",
            notes=self.notes.toPlainText().strip(),
            comments=self.comments.toPlainText().strip(),
            style_musical=self.style_musical.text().strip(),
            description=self.description.toPlainText().strip(),
            logo_path=self.logo_path.text().strip(),
            photo_path=self.photo_path.text().strip(),
            # Reseaux sociaux : pas encore exposes dans ce dialogue (hors
            # perimetre de la nouvelle structure a onglets), valeur deja
            # enregistree conservee telle quelle.
            facebook=self._source_artist.facebook if self._source_artist else "",
            instagram=self._source_artist.instagram if self._source_artist else "",
            youtube=self._source_artist.youtube if self._source_artist else "",
            created_at=self._source_artist.created_at if self._source_artist else None,
            updated_at=self._source_artist.updated_at if self._source_artist else None,
        )

        self.accept()

    def _fill_form(self, artist: Artist) -> None:
        self.legal_name.setText(artist.legal_name or "")
        self.first_name.setText(artist.first_name or "")
        self.stage_name.setText(artist.stage_name or "")
        self.birth_date.setText(artist.birth_date or "")
        self.birth_place.setText(artist.birth_place or "")
        self.social_number.setText(artist.social_number or "")
        self.conges_spectacle_number.setText(artist.conges_spectacle_number or "")

        # (artist.status or "") : une fiche ancienne peut porter NULL en base
        # (-> None en Python) - QComboBox.findText() exige une chaine, jamais
        # None (meme categorie de bug que artist_service._validate(), deja
        # corrigee : ne jamais appeler une methode texte sur une valeur
        # potentiellement None issue de SQLite).
        status_index = self.status.findText(artist.status or "")
        self.status.setCurrentIndex(status_index if status_index >= 0 else 0)

        qualification_index = self.qualification.findText(artist.qualification or "")
        self.qualification.setCurrentIndex(qualification_index if qualification_index >= 0 else 0)

        self.address.setText(artist.address or "")
        self.postal_code.setText(artist.postal_code or "")
        self.city.setText(artist.city or "")
        self.phone.setText(artist.phone or "")
        self.email.setText(artist.email or "")
        self.site_internet.setText(artist.site_internet or "")

        self.instrument.setText(artist.instrument or "")
        self.secondary_instruments.setText(artist.secondary_instruments or "")
        self.style_musical.setText(artist.style_musical or "")
        self.description.setPlainText(artist.description or "")
        self.logo_path.setText(artist.logo_path or "")
        self.photo_path.setText(artist.photo_path or "")

        self.notes.setPlainText(artist.notes or "")
        self.comments.setPlainText(artist.comments or "")
