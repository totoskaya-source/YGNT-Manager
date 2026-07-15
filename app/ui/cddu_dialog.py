from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.contracts.pdf_converter import PdfConversionTimeoutError
from app.models.contrat_cddu import ContratCddu
from app.models.prestation import Prestation
from app.services.artist_service import ArtistService
from app.services.contrat_cddu_service import ContratCdduService
from app.services.formation_artiste_service import FormationArtisteService
from app.services.organization_service import OrganizationService
from app.services.prestation_participant_service import PrestationParticipantService
from app.services.prestation_service import PrestationService
from app.ui.background_task import run_task_with_progress
from app.ui.dialogs import notify_error, notify_success, open_folder
from app.ui.theme import required_label

DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 850


class CdduDialog(QDialog):
    """Dialogue de creation/modification d'un Contrat de travail (CDDU).

    Sprint 17.0 : uniquement le cas principal (1 prestation -> 1 artiste ->
    1 contrat), sur le meme socle ergonomique que ContractDialog. La
    mensualisation, la generation multiple et la signature electronique ne
    sont pas couvertes ici (docs/CDDU_ARCHITECTURE.md)."""

    STATUS_CHOICES = (
        ("draft", "Brouillon"),
        ("validated", "Validé"),
        ("pdf_generated", "PDF généré"),
    )

    def __init__(
        self,
        parent: Any = None,
        contrat: ContratCddu | None = None,
        service: ContratCdduService | None = None,
        artist_service: ArtistService | None = None,
        prestation_service: PrestationService | None = None,
        organization_service: OrganizationService | None = None,
        participant_service: PrestationParticipantService | None = None,
        formation_composition_service: FormationArtisteService | None = None,
        initial_prestation_id: int | None = None,
    ) -> None:
        super().__init__(parent)

        self.service = service or ContratCdduService()
        self.artist_service = artist_service or ArtistService()
        self.prestation_service = prestation_service or PrestationService()
        self.organization_service = organization_service or OrganizationService()
        self.participant_service = participant_service or PrestationParticipantService()
        self.formation_composition_service = formation_composition_service or FormationArtisteService()

        self._source_contrat = contrat
        # initial_prestation_id permet de pre-selectionner la prestation (ex.
        # depuis le bouton "Creer un CDDU" de PrestationsPage, Sprint 20)
        # sans basculer le dialogue en mode "modification" - meme principe
        # que initial_devis/initial_contract/initial_facture.
        self.contrat = contrat or ContratCddu(
            numero=self.service.next_contrat_number(),
            prestation_id=initial_prestation_id,
        )
        self._selected_prestation: Prestation | None = None
        # Sprint 20.1 : instantane de la qualification et du prenom, meme
        # principe que les autres champs artiste_* (voir
        # _on_artist_selected/_fill_form), sans widget dedie dans ce dialogue.
        self._artiste_qualification: str = ""
        self._artiste_prenom: str = ""

        self.setWindowTitle("Modifier un CDDU" if contrat else "Nouveau CDDU")
        self.setMinimumSize(900, 600)

        self._settings = QSettings("YGNTManager", "CdduDialog")
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
        self._build_prestation_tab()
        self._build_defraiements_tab()
        self._build_preview_tab()

        layout.addLayout(self._build_document_actions())

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setText("Enregistrer")
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText("Annuler")
        self.buttons.accepted.connect(self.save)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        # ===== Initialisation des donnees, dans un ordre precis =====
        # 1) items des listes deroulantes (sans effet de bord) ; 2) resolution
        # de la prestation deja liee (edition) pour l'affichage lecture seule
        # de l'onglet Prestation et la liste des participants ; 3) remplissage
        # du formulaire depuis l'instantane deja enregistre (jamais ecrase par
        # les fiches actuelles) ; 4) pour un NOUVEAU CDDU seulement, pre-
        # remplissage reactif depuis la premiere prestation/le premier
        # artiste ; 5) connexion des signaux, uniquement apres coup - un
        # changement interactif de l'utilisateur declenche l'auto-remplissage,
        # jamais le chargement initial (meme principe que ContractDialog).
        self._reload_prestation_choices()

        if self.contrat.prestation_id is not None:
            self._selected_prestation = self.prestation_service.get_prestation(self.contrat.prestation_id)
        self._refresh_prestation_display(self._selected_prestation)
        self._reload_artist_choices(self.contrat.prestation_id)

        self._fill_form(self.contrat)

        if self._source_contrat is None:
            self._on_prestation_selected(self.prestation_combo.currentIndex())

        self._refresh_preview()
        self._sync_document_buttons()
        self._update_close_button()

        self.prestation_combo.currentIndexChanged.connect(self._on_prestation_selected)
        self.artist_combo.currentIndexChanged.connect(self._on_artist_selected)
        self.tabs.currentChanged.connect(self._on_tab_changed)

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

        self.status = QComboBox()
        for value, label in self.STATUS_CHOICES:
            self.status.addItem(label, value)

        self.salaire_brut = QDoubleSpinBox()
        self.salaire_brut.setMaximum(1000000)
        self.salaire_brut.setDecimals(2)
        self.salaire_brut.setSuffix(" EUR")

        self.fonction = QLineEdit()
        self.fonction.setPlaceholderText("Ex : Guitariste, Technicien son...")

        form.addRow("Référence", self.reference)
        form.addRow("Statut", self.status)
        form.addRow("Salaire brut", self.salaire_brut)
        form.addRow("Fonction", self.fonction)

        self.tabs.addTab(self._wrap_in_scroll(content), "Général")

    def _build_artist_tab(self) -> None:
        content = QWidget()
        layout = QVBoxLayout(content)

        top = QHBoxLayout()
        top.addWidget(QLabel(required_label("Artiste")))
        self.artist_combo = QComboBox()
        top.addWidget(self.artist_combo, 1)

        self.btn_add_formation_participant = QPushButton("+ Ajouter la formation de la prestation")
        self.btn_add_formation_participant.setVisible(False)
        self.btn_add_formation_participant.clicked.connect(self._add_formation_as_participant)
        top.addWidget(self.btn_add_formation_participant)
        layout.addLayout(top)

        hint = QLabel(
            "Seuls les artistes enregistrés dans l'équipe de la prestation "
            "choisie (onglet Prestation) sont proposés ici."
        )
        hint.setWordWrap(True)
        layout.addWidget(hint)

        form = QFormLayout()

        self.artiste_nom = QLineEdit()
        self.artiste_adresse = QLineEdit()
        self.artiste_postal_code = QLineEdit()
        self.artiste_city = QLineEdit()
        self.artiste_phone = QLineEdit()
        self.artiste_email = QLineEdit()
        self.artiste_date_naissance = QLineEdit()
        self.artiste_lieu_naissance = QLineEdit()
        self.artiste_numero_secu = QLineEdit()
        self.artiste_numero_conges_spectacle = QLineEdit()

        for field in (
            self.artiste_nom,
            self.artiste_adresse,
            self.artiste_postal_code,
            self.artiste_city,
            self.artiste_phone,
            self.artiste_email,
            self.artiste_date_naissance,
            self.artiste_lieu_naissance,
            self.artiste_numero_secu,
            self.artiste_numero_conges_spectacle,
        ):
            field.setReadOnly(True)

        form.addRow("Nom", self.artiste_nom)
        form.addRow("Adresse", self.artiste_adresse)
        form.addRow("Code postal", self.artiste_postal_code)
        form.addRow("Ville", self.artiste_city)
        form.addRow("Téléphone", self.artiste_phone)
        form.addRow("Email", self.artiste_email)
        form.addRow("Date de naissance", self.artiste_date_naissance)
        form.addRow("Lieu de naissance", self.artiste_lieu_naissance)
        form.addRow("Numéro de sécurité sociale", self.artiste_numero_secu)
        form.addRow("Numéro de congés spectacle", self.artiste_numero_conges_spectacle)

        layout.addLayout(form)

        self.tabs.addTab(self._wrap_in_scroll(content), "Artiste")

    def _build_prestation_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.prestation_combo = QComboBox()

        self.prestation_formation = QLineEdit()
        self.prestation_date = QLineEdit()
        self.prestation_lieu_display = QLineEdit()
        self.prestation_organisateur = QLineEdit()

        for field in (
            self.prestation_formation,
            self.prestation_date,
            self.prestation_lieu_display,
            self.prestation_organisateur,
        ):
            field.setReadOnly(True)

        form.addRow("Prestation", self.prestation_combo)
        form.addRow("Formation", self.prestation_formation)
        form.addRow("Date", self.prestation_date)
        form.addRow("Lieu", self.prestation_lieu_display)
        form.addRow("Organisateur", self.prestation_organisateur)

        self.tabs.addTab(self._wrap_in_scroll(content), "Prestation")

    def _build_defraiements_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.defraiement_deplacement = QDoubleSpinBox()
        self.defraiement_hebergement = QDoubleSpinBox()
        self.defraiement_repas = QDoubleSpinBox()
        self.defraiement_autres_montant = QDoubleSpinBox()

        for field in (
            self.defraiement_deplacement,
            self.defraiement_hebergement,
            self.defraiement_repas,
            self.defraiement_autres_montant,
        ):
            field.setMaximum(1000000)
            field.setDecimals(2)
            field.setSuffix(" EUR")

        self.defraiement_autres_libelle = QLineEdit()
        self.defraiement_autres_libelle.setPlaceholderText("Libellé (ex : Matériel, Parking...)")

        form.addRow("Déplacement", self.defraiement_deplacement)
        form.addRow("Hébergement", self.defraiement_hebergement)
        form.addRow("Repas", self.defraiement_repas)
        form.addRow("Autres (libellé)", self.defraiement_autres_libelle)
        form.addRow("Autres (montant)", self.defraiement_autres_montant)

        self.tabs.addTab(self._wrap_in_scroll(content), "Défraiements")

    def _build_preview_tab(self) -> None:
        content = QWidget()
        layout = QVBoxLayout(content)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)

        self.tabs.addTab(content, "Aperçu")

    def _build_document_actions(self) -> QHBoxLayout:
        actions = QHBoxLayout()
        actions.setSpacing(8)

        self.btn_generate_docx = QPushButton("Générer DOCX")
        self.btn_generate_pdf = QPushButton("Générer PDF")
        self.btn_open_docx = QPushButton("Ouvrir DOCX")
        self.btn_open_pdf = QPushButton("Ouvrir PDF")
        self.btn_open_folder = QPushButton("📂 Ouvrir le dossier des documents")

        self.btn_generate_docx.clicked.connect(self.generate_docx)
        self.btn_generate_pdf.clicked.connect(self.generate_pdf)
        self.btn_open_docx.clicked.connect(self.open_docx)
        self.btn_open_pdf.clicked.connect(self.open_pdf)
        self.btn_open_folder.clicked.connect(self.open_documents_folder)

        actions.addWidget(self.btn_generate_docx)
        actions.addWidget(self.btn_generate_pdf)
        actions.addWidget(self.btn_open_docx)
        actions.addWidget(self.btn_open_pdf)
        actions.addWidget(self.btn_open_folder)
        actions.addStretch()

        return actions

    # ===== Prestation =====

    def _reload_prestation_choices(self) -> None:
        self.prestation_combo.addItem("(Choisissez une prestation)", None)
        for prestation in self.prestation_service.list_prestations():
            label = f"{prestation.reference} - {prestation.nom}" if prestation.reference else prestation.nom
            self.prestation_combo.addItem(label, prestation.id)

    def _on_prestation_selected(self, _index: int) -> None:
        prestation_id = self.prestation_combo.currentData()
        self._selected_prestation = (
            self.prestation_service.get_prestation(prestation_id) if prestation_id is not None else None
        )
        self._refresh_prestation_display(self._selected_prestation)
        self._reload_artist_choices(prestation_id)
        self._on_artist_selected(self.artist_combo.currentIndex())

    def _refresh_prestation_display(self, prestation: Prestation | None) -> None:
        if prestation is None:
            self.prestation_formation.setText("")
            self.prestation_date.setText("")
            self.prestation_lieu_display.setText("")
            self.prestation_organisateur.setText("")
            return

        formation = self.artist_service.get_artist(prestation.artist_id) if prestation.artist_id else None
        self.prestation_formation.setText((formation.stage_name or formation.legal_name) if formation else "")

        self.prestation_date.setText(prestation.date_debut or "")

        lieu = ", ".join(part for part in (prestation.lieu_nom, prestation.lieu_city) if part)
        self.prestation_lieu_display.setText(lieu)

        organisateur = (
            self.organization_service.get_organization(prestation.organization_id)
            if prestation.organization_id
            else None
        )
        self.prestation_organisateur.setText(organisateur.name if organisateur else "")

    # ===== Artiste (filtre sur prestation_participants) =====

    def _reload_artist_choices(self, prestation_id: int | None) -> None:
        self.artist_combo.blockSignals(True)
        self.artist_combo.clear()

        if prestation_id is None:
            self.artist_combo.addItem("(Choisissez d'abord une prestation)", None)
            self.artist_combo.setEnabled(False)
            self.btn_add_formation_participant.setVisible(False)
            self.artist_combo.blockSignals(False)
            return

        participants = self.participant_service.list_participants(prestation_id)
        self.artist_combo.setEnabled(True)

        if not participants:
            self.artist_combo.addItem("(Aucun participant enregistré pour cette prestation)", None)
            can_seed = bool(
                self._selected_prestation
                and (self._selected_prestation.formation_id or self._selected_prestation.artist_id)
            )
            self.btn_add_formation_participant.setVisible(can_seed)
        else:
            self.btn_add_formation_participant.setVisible(False)
            for participant in participants:
                artist = self.artist_service.get_artist(participant.artiste_id)
                label = (artist.stage_name or artist.legal_name) if artist else f"Artiste #{participant.artiste_id}"
                if participant.role:
                    label = f"{label} ({participant.role})"
                self.artist_combo.addItem(label, participant.artiste_id)

        self.artist_combo.blockSignals(False)

    def _add_formation_as_participant(self) -> None:
        """Peuple rapidement l'equipe de la prestation choisie, pour pouvoir
        creer un CDDU sans repasser par l'onglet Formation de la Prestation.

        Sprint 20 : priorite a prestation.formation_id (vraie Formation) -
        importe alors TOUS ses membres reels (formation_artistes), pas
        seulement un artiste unique. Comportement historique (un seul
        artiste via artist_id) preserve pour une prestation ancienne."""
        if self._selected_prestation is None:
            return

        if self._selected_prestation.formation_id is not None:
            members = self.formation_composition_service.list_composition(self._selected_prestation.formation_id)
            for member in members:
                try:
                    self.participant_service.add_participant(
                        self._selected_prestation.id,
                        member.artiste_id,
                        role=member.role,
                        ordre=member.ordre,
                    )
                except ValueError:
                    pass  # deja participant : rien a faire
        elif self._selected_prestation.artist_id is not None:
            try:
                self.participant_service.add_participant(
                    self._selected_prestation.id,
                    self._selected_prestation.artist_id,
                )
            except ValueError:
                pass  # deja participant : rien a faire, on rafraichit simplement

        self._reload_artist_choices(self._selected_prestation.id)
        self._on_artist_selected(self.artist_combo.currentIndex())

    def _on_artist_selected(self, _index: int) -> None:
        artist_id = self.artist_combo.currentData()
        if artist_id is None:
            for field in (
                self.artiste_nom,
                self.artiste_adresse,
                self.artiste_postal_code,
                self.artiste_city,
                self.artiste_phone,
                self.artiste_email,
                self.artiste_date_naissance,
                self.artiste_lieu_naissance,
                self.artiste_numero_secu,
                self.artiste_numero_conges_spectacle,
            ):
                field.setText("")
            self._artiste_qualification = ""
            self._artiste_prenom = ""
            return

        artist = self.artist_service.get_artist(artist_id)
        if artist is None:
            return

        self.artiste_nom.setText(artist.legal_name or artist.stage_name or "")
        self.artiste_adresse.setText(artist.address or "")
        self.artiste_postal_code.setText(artist.postal_code or "")
        self.artiste_city.setText(artist.city or "")
        self.artiste_phone.setText(artist.phone or "")
        self.artiste_email.setText(artist.email or "")
        self.artiste_date_naissance.setText(artist.birth_date or "")
        self.artiste_lieu_naissance.setText(artist.birth_place or "")
        self.artiste_numero_secu.setText(artist.social_number or "")
        self.artiste_numero_conges_spectacle.setText(artist.conges_spectacle_number or "")
        self.fonction.setText(artist.instrument or "")
        # Qualification (Sprint 20.1) et prenom : instantanees comme tous les
        # autres champs artiste_* ci-dessus, mais sans widget dedie dans ce
        # dialogue - conservees ici pour etre ecrites par _build_contrat(),
        # sinon jamais transmises au document (meme bug que qualification,
        # corrige a l'identique).
        self._artiste_qualification = artist.qualification or ""
        self._artiste_prenom = artist.first_name or ""

    # ===== Onglet Apercu =====

    def _on_tab_changed(self, _index: int) -> None:
        if self.tabs.currentWidget() is self.preview_text.parent():
            self._refresh_preview()

    def _refresh_preview(self) -> None:
        self.preview_text.setPlainText(self.service.preview(self._build_contrat()))

    def _save_geometry(self) -> None:
        self._settings.setValue("geometry", self.saveGeometry())

    # ===== Generation / ouverture DOCX et PDF =====

    def _sync_document_buttons(self) -> None:
        has_saved = bool(self._source_contrat and self._source_contrat.id is not None)
        self.btn_generate_docx.setEnabled(has_saved)
        self.btn_generate_pdf.setEnabled(has_saved)

        has_docx = bool(
            self._source_contrat
            and self._source_contrat.docx_path
            and Path(self._source_contrat.docx_path).exists()
        )
        has_pdf = bool(
            self._source_contrat
            and self._source_contrat.pdf_path
            and Path(self._source_contrat.pdf_path).exists()
        )
        self.btn_open_docx.setEnabled(has_docx)
        self.btn_open_pdf.setEnabled(has_pdf)

    def _update_close_button(self) -> None:
        has_saved = bool(self._source_contrat and self._source_contrat.id is not None)
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(
            "Fermer" if has_saved else "Annuler"
        )

    def open_documents_folder(self) -> None:
        open_folder(self.service.exports_dir)

    def _refresh_source_contrat(self) -> None:
        if self._source_contrat is None or self._source_contrat.id is None:
            return

        refreshed = self.service.get_contrat(self._source_contrat.id)
        if refreshed is not None:
            self._source_contrat = refreshed
            self.contrat = refreshed

        self._sync_document_buttons()

    def generate_docx(self) -> None:
        if self._source_contrat is None or self._source_contrat.id is None:
            QMessageBox.information(self, "Génération", "Enregistrez d'abord le CDDU.")
            return

        try:
            self.service.generate_docx(self._source_contrat.id)
        except Exception as exc:
            notify_error(self, str(exc))
            return

        self._refresh_source_contrat()
        self._refresh_preview()
        notify_success(self, "Document DOCX généré.")

    def generate_pdf(self) -> None:
        if self._source_contrat is None or self._source_contrat.id is None:
            QMessageBox.information(self, "Export PDF", "Enregistrez d'abord le CDDU.")
            return

        contrat_id = self._source_contrat.id

        def on_success(_result: object) -> None:
            self._refresh_source_contrat()
            self._sync_status_display()
            self._refresh_preview()
            notify_success(self, "Document PDF généré.")

        def on_error(exc: Exception) -> None:
            if isinstance(exc, PdfConversionTimeoutError):
                QMessageBox.warning(
                    self,
                    "Génération PDF",
                    "La generation du PDF semble bloquée.\n\n"
                    "Veuillez vérifier qu'aucune fenêtre Microsoft Word "
                    "n'attend votre intervention.",
                )
                return
            notify_error(self, str(exc))

        run_task_with_progress(
            self,
            "Génération du PDF...\nVeuillez patienter.",
            lambda: self.service.export_pdf(contrat_id),
            on_success,
            on_error,
        )

    def _sync_status_display(self) -> None:
        # Le statut peut avoir avance automatiquement (Brouillon -> PDF
        # genere) lors de l'export PDF (docs/CDDU_ARCHITECTURE.md §12) :
        # refleter ce changement dans le combo, sans jamais le faire reculer.
        if self._source_contrat is None:
            return
        status_index = self.status.findData(self._source_contrat.status)
        if status_index >= 0:
            self.status.setCurrentIndex(status_index)

    def open_docx(self) -> None:
        if self._source_contrat is None or self._source_contrat.id is None:
            QMessageBox.information(self, "Document", "Enregistrez d'abord le CDDU.")
            return

        try:
            self.service.open_document(self._source_contrat.id)
        except FileNotFoundError as exc:
            QMessageBox.warning(self, "Document", str(exc))

    def open_pdf(self) -> None:
        if self._source_contrat is None or self._source_contrat.id is None:
            QMessageBox.information(self, "PDF", "Enregistrez d'abord le CDDU.")
            return

        try:
            self.service.open_pdf(self._source_contrat.id)
        except FileNotFoundError as exc:
            QMessageBox.warning(self, "PDF", str(exc))

    # ===== Sauvegarde =====

    def save(self) -> None:
        contrat = self._build_contrat()
        is_new = contrat.id is None

        try:
            if is_new:
                contrat.id = self.service.create_contrat(contrat)

                # Cas principal du sprint (1 prestation -> 1 artiste -> 1
                # contrat) : aucune UI de gestion des dates n'existe encore,
                # donc l'unique ligne contrat_cddu_dates est creee ici,
                # automatiquement, a partir de la date de la prestation
                # choisie (docs/CDDU_ARCHITECTURE.md §6).
                if self._selected_prestation is not None and self._selected_prestation.date_debut:
                    self.service.add_date(
                        contrat.id,
                        self._selected_prestation.date_debut,
                        prestation_id=self._selected_prestation.id,
                        nombre_cachets=1,
                    )
            else:
                self.service.update_contrat(contrat)
        except ValueError as exc:
            QMessageBox.warning(self, "CDDU invalide", str(exc))
            return

        saved = self.service.get_contrat(contrat.id)
        if saved is not None:
            contrat = saved

        self.contrat = contrat
        self._source_contrat = contrat

        # Le dialogue reste ouvert apres l'enregistrement : les documents
        # DOCX/PDF deviennent immediatement generables, meme ergonomie que
        # ContractDialog (Sprint 12.0).
        self.setWindowTitle("Modifier un CDDU")
        self._sync_document_buttons()
        self._update_close_button()
        self._refresh_preview()

        notify_success(self, "CDDU créé." if is_new else "CDDU modifié.")

    def _build_contrat(self) -> ContratCddu:
        source = self._source_contrat
        prestation = self._selected_prestation

        return ContratCddu(
            id=source.id if source else None,
            numero=self.reference.text().strip(),
            prestation_id=self.prestation_combo.currentData(),
            artist_id=self.artist_combo.currentData(),
            # Instantane Producteur : jamais saisi dans ce dialogue, jamais
            # recalcule ici (meme principe que ContractDialog). Un nouveau
            # CDDU le recoit du Producteur actif dans
            # ContratCdduService.create_contrat ; un CDDU existant conserve
            # tel quel l'instantane deja enregistre.
            producteur_id=source.producteur_id if source else None,
            producteur_nom=source.producteur_nom if source else "",
            producteur_forme_juridique=source.producteur_forme_juridique if source else "",
            producteur_adresse=source.producteur_adresse if source else "",
            producteur_postal_code=source.producteur_postal_code if source else "",
            producteur_city=source.producteur_city if source else "",
            producteur_siret=source.producteur_siret if source else "",
            producteur_ape=source.producteur_ape if source else "",
            producteur_licence=source.producteur_licence if source else "",
            producteur_convention_collective=source.producteur_convention_collective if source else "",
            producteur_representant=source.producteur_representant if source else "",
            producteur_fonction=source.producteur_fonction if source else "",
            producteur_email=source.producteur_email if source else "",
            producteur_phone=source.producteur_phone if source else "",
            artiste_nom=self.artiste_nom.text().strip(),
            artiste_adresse=self.artiste_adresse.text().strip(),
            artiste_postal_code=self.artiste_postal_code.text().strip(),
            artiste_city=self.artiste_city.text().strip(),
            artiste_phone=self.artiste_phone.text().strip(),
            artiste_email=self.artiste_email.text().strip(),
            artiste_date_naissance=self.artiste_date_naissance.text().strip(),
            artiste_lieu_naissance=self.artiste_lieu_naissance.text().strip(),
            artiste_numero_secu=self.artiste_numero_secu.text().strip(),
            artiste_numero_conges_spectacle=self.artiste_numero_conges_spectacle.text().strip(),
            artiste_fonction=self.fonction.text().strip(),
            artiste_qualification=self._artiste_qualification,
            artiste_prenom=self._artiste_prenom,
            prestation_reference=(
                prestation.reference if prestation else (source.prestation_reference if source else "")
            ),
            prestation_objet=(prestation.nom if prestation else (source.prestation_objet if source else "")),
            prestation_lieu=(prestation.lieu_nom if prestation else (source.prestation_lieu if source else "")),
            prestation_ville=(prestation.lieu_city if prestation else (source.prestation_ville if source else "")),
            # Toujours vide : aucune logique de calcul ou de generation
            # (docs/CDDU_ARCHITECTURE.md §9), reconfirme par le Service de
            # toute facon.
            numero_objet="",
            remuneration_brute=self.salaire_brut.value(),
            defraiement_deplacement=self.defraiement_deplacement.value(),
            defraiement_hebergement=self.defraiement_hebergement.value(),
            defraiement_repas=self.defraiement_repas.value(),
            defraiement_autres_libelle=self.defraiement_autres_libelle.text().strip(),
            defraiement_autres_montant=self.defraiement_autres_montant.value(),
            defraiement_montant_libre_libelle=source.defraiement_montant_libre_libelle if source else "",
            defraiement_montant_libre_montant=source.defraiement_montant_libre_montant if source else 0.0,
            observations=source.observations if source else "",
            ville_signature=source.ville_signature if source else "",
            date_signature=source.date_signature if source else "",
            docx_path=source.docx_path if source else "",
            pdf_path=source.pdf_path if source else "",
            status=str(self.status.currentData()),
            created_at=source.created_at if source else None,
            updated_at=source.updated_at if source else None,
            generated_at=source.generated_at if source else None,
        )

    def _fill_form(self, contrat: ContratCddu) -> None:
        self.reference.setText(contrat.numero or self.service.next_contrat_number())

        prestation_index = self.prestation_combo.findData(contrat.prestation_id)
        self.prestation_combo.setCurrentIndex(prestation_index if prestation_index >= 0 else 0)

        artist_index = self.artist_combo.findData(contrat.artist_id)
        self.artist_combo.setCurrentIndex(artist_index if artist_index >= 0 else 0)

        self.artiste_nom.setText(contrat.artiste_nom or "")
        self.artiste_adresse.setText(contrat.artiste_adresse or "")
        self.artiste_postal_code.setText(contrat.artiste_postal_code or "")
        self.artiste_city.setText(contrat.artiste_city or "")
        self.artiste_phone.setText(contrat.artiste_phone or "")
        self.artiste_email.setText(contrat.artiste_email or "")
        self.artiste_date_naissance.setText(contrat.artiste_date_naissance or "")
        self.artiste_lieu_naissance.setText(contrat.artiste_lieu_naissance or "")
        self.artiste_numero_secu.setText(contrat.artiste_numero_secu or "")
        self.artiste_numero_conges_spectacle.setText(contrat.artiste_numero_conges_spectacle or "")

        self.fonction.setText(contrat.artiste_fonction or "")
        # Instantane fige (Sprint 20.1) : un CDDU deja enregistre conserve sa
        # qualification et son prenom tels quels, jamais re-derives de la
        # fiche Artiste (meme principe que les autres champs artiste_*
        # ci-dessus).
        self._artiste_qualification = contrat.artiste_qualification or ""
        self._artiste_prenom = contrat.artiste_prenom or ""
        self.salaire_brut.setValue(float(contrat.remuneration_brute or 0))

        status_index = self.status.findData(contrat.status or "draft")
        self.status.setCurrentIndex(status_index if status_index >= 0 else 0)

        self.defraiement_deplacement.setValue(float(contrat.defraiement_deplacement or 0))
        self.defraiement_hebergement.setValue(float(contrat.defraiement_hebergement or 0))
        self.defraiement_repas.setValue(float(contrat.defraiement_repas or 0))
        self.defraiement_autres_libelle.setText(contrat.defraiement_autres_libelle or "")
        self.defraiement_autres_montant.setValue(float(contrat.defraiement_autres_montant or 0))
