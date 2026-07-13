from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QDate, QSettings
from PySide6.QtWidgets import (
    QAbstractSpinBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
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
from app.models.facture import Facture
from app.services.artist_service import ArtistService
from app.services.facture_service import FactureService
from app.services.organization_service import OrganizationService
from app.ui.background_task import run_task_with_progress
from app.ui.dialogs import notify_success, open_folder

DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 850


class FactureDialog(QDialog):
    def __init__(
        self,
        parent: Any = None,
        facture: Facture | None = None,
        service: FactureService | None = None,
        artist_service: ArtistService | None = None,
        organization_service: OrganizationService | None = None,
        initial_facture: Facture | None = None,
    ) -> None:
        super().__init__(parent)

        self.service = service or FactureService()
        self.artist_service = artist_service or ArtistService()
        self.organization_service = organization_service or OrganizationService()
        self._source_facture = facture
        # initial_facture permet de pre-remplir une NOUVELLE facture (ex. depuis
        # une prestation ou un contrat) sans basculer le dialogue en mode
        # "modification".
        self._initial_prestation_id = initial_facture.prestation_id if initial_facture else None
        self._initial_contract_id = initial_facture.contract_id if initial_facture else None
        self.facture = facture or initial_facture or Facture(facture_number=self.service.next_facture_number())

        self.setWindowTitle("Modifier une facture" if facture else "Nouvelle facture")
        self.setMinimumSize(900, 600)

        self._settings = QSettings("YGNTManager", "FactureDialog")
        saved_geometry = self._settings.value("geometry")
        if saved_geometry is not None:
            self.restoreGeometry(saved_geometry)
        else:
            self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self._build_general_tab()
        self._build_formation_tab()
        self._build_organizer_tab()
        self._build_performance_tab()
        self._build_financial_tab()
        self._build_preview_tab()

        # La date generale et la date de prestation representent la meme
        # information : elles restent synchronisees dans les deux sens.
        self.date_general.dateChanged.connect(self.date_prestation.setDate)
        self.date_prestation.dateChanged.connect(self.date_general.setDate)

        # Actions document (DOCX/PDF) : disponibles uniquement une fois la facture
        # enregistree (un identifiant est necessaire pour nommer/retrouver les
        # fichiers), meme ergonomie que le module Devis.
        layout.addLayout(self._build_document_actions())

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

        self._fill_form(self.facture)

        if self._source_facture is None:
            # Nouvelle facture : on derive les details depuis les fiches Formation
            # et Organisateur liees. Pour une facture existante, l'instantane deja
            # enregistre est conserve tel quel (jamais ecrase par les donnees
            # actuelles des fiches) - meme principe que Contrats/Devis.
            self._on_formation_selected(self.formation_combo.currentIndex())
            self._on_organization_selected(self.organization_combo.currentIndex())

        self._recalculate_total()
        self._refresh_preview()
        self._sync_document_buttons()
        self._update_close_button()

        # Connectes apres le remplissage initial : un changement manuel de
        # l'utilisateur declenche l'auto-remplissage, pas le chargement du formulaire.
        self.formation_combo.currentIndexChanged.connect(self._on_formation_selected)
        self.organization_combo.currentIndexChanged.connect(self._on_organization_selected)
        self.tabs.currentChanged.connect(self._on_tab_changed)

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

        self.facture_number = QLineEdit()
        self.facture_number.setReadOnly(True)

        self.date_general = QDateEdit()
        self.date_general.setCalendarPopup(True)
        self.date_general.setDate(QDate.currentDate())

        self.status = QComboBox()
        for code, label in FactureService.STATUSES.items():
            self.status.addItem(label, code)

        form.addRow("Reference", self.facture_number)
        form.addRow("Date", self.date_general)
        form.addRow("Statut", self.status)

        self.tabs.addTab(self._wrap_in_scroll(content), "General")

    def _build_formation_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.formation_combo = QComboBox()
        self._reload_formation_choices()

        self.formation_nom = QLineEdit()
        self.formation_nom.setReadOnly(True)
        self.formation_adresse = QLineEdit()
        self.formation_adresse.setReadOnly(True)
        self.formation_postal_code = QLineEdit()
        self.formation_postal_code.setReadOnly(True)
        self.formation_city = QLineEdit()
        self.formation_city.setReadOnly(True)
        self.formation_phone = QLineEdit()
        self.formation_phone.setReadOnly(True)
        self.formation_email = QLineEdit()
        self.formation_email.setReadOnly(True)
        self.formation_site_internet = QLineEdit()
        self.formation_site_internet.setReadOnly(True)
        self.formation_siren = QLineEdit()
        self.formation_siren.setReadOnly(True)
        self.formation_siret = QLineEdit()
        self.formation_siret.setReadOnly(True)
        self.formation_ape = QLineEdit()
        self.formation_ape.setReadOnly(True)
        self.formation_licence = QLineEdit()
        self.formation_licence.setReadOnly(True)
        self.formation_iban = QLineEdit()
        self.formation_iban.setReadOnly(True)
        self.formation_bic = QLineEdit()
        self.formation_bic.setReadOnly(True)
        self.formation_social_number = QLineEdit()
        self.formation_social_number.setReadOnly(True)
        self.formation_notes = QTextEdit()
        self.formation_notes.setFixedHeight(70)
        self.formation_notes.setReadOnly(True)

        form.addRow("Formation", self.formation_combo)
        form.addRow("Nom", self.formation_nom)
        form.addRow("Adresse", self.formation_adresse)
        form.addRow("Code postal", self.formation_postal_code)
        form.addRow("Ville", self.formation_city)
        form.addRow("Telephone", self.formation_phone)
        form.addRow("Email", self.formation_email)
        form.addRow("Site internet", self.formation_site_internet)
        form.addRow("SIREN", self.formation_siren)
        form.addRow("SIRET", self.formation_siret)
        form.addRow("Code APE", self.formation_ape)
        form.addRow("Licence", self.formation_licence)
        form.addRow("IBAN", self.formation_iban)
        form.addRow("BIC", self.formation_bic)
        form.addRow("Numero de securite sociale", self.formation_social_number)
        form.addRow("Notes", self.formation_notes)

        self.tabs.addTab(self._wrap_in_scroll(content), "Formation")

    def _build_organizer_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.organization_combo = QComboBox()
        self._reload_organization_choices()

        self.organisateur_nom = QLineEdit()
        self.organisateur_nom.setReadOnly(True)
        self.organisateur_forme = QLineEdit()
        self.organisateur_forme.setReadOnly(True)
        self.organisateur_adresse = QLineEdit()
        self.organisateur_adresse.setReadOnly(True)
        self.organisateur_postal_code = QLineEdit()
        self.organisateur_postal_code.setReadOnly(True)
        self.organisateur_city = QLineEdit()
        self.organisateur_city.setReadOnly(True)
        self.organisateur_siret = QLineEdit()
        self.organisateur_siret.setReadOnly(True)
        self.organisateur_phone = QLineEdit()
        self.organisateur_phone.setReadOnly(True)
        self.organisateur_email = QLineEdit()
        self.organisateur_email.setReadOnly(True)
        self.organisateur_site_internet = QLineEdit()
        self.organisateur_site_internet.setReadOnly(True)
        self.organisateur_ape = QLineEdit()
        self.organisateur_ape.setReadOnly(True)
        self.organisateur_licence = QLineEdit()
        self.organisateur_licence.setReadOnly(True)
        self.organisateur_tva = QLineEdit()
        self.organisateur_tva.setReadOnly(True)
        self.organisateur_representant = QLineEdit()
        self.organisateur_representant.setReadOnly(True)
        self.organisateur_fonction = QLineEdit()
        self.organisateur_fonction.setReadOnly(True)
        self.organisateur_iban = QLineEdit()
        self.organisateur_iban.setReadOnly(True)
        self.organisateur_bic = QLineEdit()
        self.organisateur_bic.setReadOnly(True)
        self.organisateur_notes = QTextEdit()
        self.organisateur_notes.setFixedHeight(70)
        self.organisateur_notes.setReadOnly(True)

        form.addRow("Organisateur", self.organization_combo)
        form.addRow("Nom", self.organisateur_nom)
        form.addRow("Forme juridique", self.organisateur_forme)
        form.addRow("Adresse", self.organisateur_adresse)
        form.addRow("Code postal", self.organisateur_postal_code)
        form.addRow("Ville", self.organisateur_city)
        form.addRow("SIRET", self.organisateur_siret)
        form.addRow("Telephone", self.organisateur_phone)
        form.addRow("Email", self.organisateur_email)
        form.addRow("Site internet", self.organisateur_site_internet)
        form.addRow("Code APE", self.organisateur_ape)
        form.addRow("Licence spectacle", self.organisateur_licence)
        form.addRow("TVA intracommunautaire", self.organisateur_tva)
        form.addRow("Representee par", self.organisateur_representant)
        form.addRow("Fonction", self.organisateur_fonction)
        form.addRow("IBAN", self.organisateur_iban)
        form.addRow("BIC", self.organisateur_bic)
        form.addRow("Notes", self.organisateur_notes)

        self.tabs.addTab(self._wrap_in_scroll(content), "Organisateur")

    def _build_performance_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.objet = QLineEdit()

        self.date_prestation = QDateEdit()
        self.date_prestation.setCalendarPopup(True)
        self.date_prestation.setDate(QDate.currentDate())

        self.lieu = QLineEdit()
        self.ville = QLineEdit()

        self.description = QTextEdit()
        self.description.setFixedHeight(90)

        form.addRow("Objet", self.objet)
        form.addRow("Date", self.date_prestation)
        form.addRow("Lieu", self.lieu)
        form.addRow("Ville", self.ville)
        form.addRow("Description", self.description)

        self.tabs.addTab(self._wrap_in_scroll(content), "Prestation")

    def _build_financial_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.montant = QDoubleSpinBox()
        self.montant.setMaximum(1000000)
        self.montant.setDecimals(2)
        self.montant.setSuffix(" EUR")

        self.tva = QLineEdit()
        self.tva.setPlaceholderText("Ex : 2,10% ou Exoneree")

        self.acompte = QDoubleSpinBox()
        self.acompte.setMaximum(1000000)
        self.acompte.setDecimals(2)
        self.acompte.setSuffix(" EUR")

        self.total = QDoubleSpinBox()
        self.total.setMinimum(-1000000)
        self.total.setMaximum(1000000)
        self.total.setDecimals(2)
        self.total.setSuffix(" EUR")
        self.total.setReadOnly(True)
        self.total.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)

        self.mode = QComboBox()
        self.mode.addItems(["Virement", "Cheque"])

        self.echeance = QLineEdit()
        self.echeance.setPlaceholderText("Ex : 30 jours apres la prestation")

        self.notes = QTextEdit()
        self.notes.setFixedHeight(90)

        # Le total (reste du) se recalcule automatiquement : montant - acompte.
        self.montant.valueChanged.connect(self._recalculate_total)
        self.acompte.valueChanged.connect(self._recalculate_total)

        form.addRow("Montant", self.montant)
        form.addRow("TVA", self.tva)
        form.addRow("Acompte", self.acompte)
        form.addRow("Total", self.total)
        form.addRow("Mode de paiement", self.mode)
        form.addRow("Echeance", self.echeance)
        form.addRow("Notes", self.notes)

        self.tabs.addTab(self._wrap_in_scroll(content), "Conditions financieres")

    def _build_preview_tab(self) -> None:
        content = QWidget()
        layout = QVBoxLayout(content)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)

        self.tabs.addTab(content, "Apercu")

    def _build_document_actions(self) -> QHBoxLayout:
        actions = QHBoxLayout()
        actions.setSpacing(8)

        self.btn_generate_docx = QPushButton("Generer DOCX")
        self.btn_generate_pdf = QPushButton("Generer PDF")
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

    # ===== Listes deroulantes Formation / Organisateur =====

    def _reload_formation_choices(self) -> None:
        self.formation_combo.addItem("(Aucun)", None)
        for artist in self.artist_service.list_artists():
            label = artist.stage_name or artist.legal_name or f"Formation #{artist.id}"
            self.formation_combo.addItem(label, artist.id)

    def _reload_organization_choices(self) -> None:
        self.organization_combo.addItem("(Aucun / saisie libre)", None)
        for organization in self.organization_service.list_organizations():
            label = organization.name or f"Organisateur #{organization.id}"
            self.organization_combo.addItem(label, organization.id)

    def _on_formation_selected(self, _index: int) -> None:
        formation_id = self.formation_combo.currentData()
        if formation_id is None:
            return

        artist = self.artist_service.get_artist(formation_id)
        if artist is None:
            return

        self.formation_nom.setText(artist.stage_name or artist.legal_name or "")
        self.formation_adresse.setText(artist.address or "")
        self.formation_postal_code.setText(artist.postal_code or "")
        self.formation_city.setText(artist.city or "")
        self.formation_phone.setText(artist.phone or "")
        self.formation_email.setText(artist.email or "")
        self.formation_site_internet.setText(artist.site_internet or "")
        self.formation_siren.setText(artist.siren or "")
        self.formation_siret.setText(artist.siret or "")
        self.formation_ape.setText(artist.ape or "")
        self.formation_licence.setText(artist.licence or "")
        self.formation_iban.setText(artist.iban or "")
        self.formation_bic.setText(artist.bic or "")
        self.formation_social_number.setText(artist.social_number or "")
        self.formation_notes.setPlainText(artist.notes or "")

    def _on_organization_selected(self, _index: int) -> None:
        organization_id = self.organization_combo.currentData()
        if organization_id is None:
            return

        organization = self.organization_service.get_organization(organization_id)
        if organization is None:
            return

        self.organisateur_nom.setText(organization.name or "")
        self.organisateur_forme.setText(organization.legal_form or "")
        self.organisateur_adresse.setText(organization.address or "")
        self.organisateur_postal_code.setText(organization.postal_code or "")
        self.organisateur_city.setText(organization.city or "")
        self.organisateur_siret.setText(organization.siret or "")
        self.organisateur_phone.setText(organization.phone or "")
        self.organisateur_email.setText(organization.email or "")
        self.organisateur_site_internet.setText(organization.site_internet or "")
        self.organisateur_ape.setText(organization.ape or "")
        self.organisateur_licence.setText(organization.licence or "")
        self.organisateur_tva.setText(organization.tva or "")
        self.organisateur_representant.setText(organization.president or "")
        self.organisateur_fonction.setText(organization.fonction or "")
        self.organisateur_iban.setText(organization.iban or "")
        self.organisateur_bic.setText(organization.bic or "")
        self.organisateur_notes.setPlainText(organization.notes or "")

    # ===== Conditions financieres =====

    def _recalculate_total(self, *_args: Any) -> None:
        self.total.setValue(round(self.montant.value() - self.acompte.value(), 2))

    # ===== Onglet Apercu =====

    def _on_tab_changed(self, _index: int) -> None:
        if self.tabs.currentWidget() is self.preview_text.parent():
            self._refresh_preview()

    def _refresh_preview(self) -> None:
        try:
            text = self.service.preview(self._build_facture())
        except ValueError as exc:
            text = f"Facture incomplete : {exc}"
        self.preview_text.setPlainText(text)

    def _save_geometry(self) -> None:
        self._settings.setValue("geometry", self.saveGeometry())

    # ===== Generation / ouverture DOCX et PDF =====

    def _sync_document_buttons(self) -> None:
        has_saved_facture = bool(self._source_facture and self._source_facture.id is not None)
        self.btn_generate_docx.setEnabled(has_saved_facture)
        self.btn_generate_pdf.setEnabled(has_saved_facture)

        has_docx = bool(
            self._source_facture
            and self._source_facture.docx_path
            and Path(self._source_facture.docx_path).exists()
        )
        has_pdf = bool(
            self._source_facture
            and self._source_facture.pdf_path
            and Path(self._source_facture.pdf_path).exists()
        )
        self.btn_open_docx.setEnabled(has_docx)
        self.btn_open_pdf.setEnabled(has_pdf)

    def _update_close_button(self) -> None:
        # Tant que rien n'est enregistre, "Annuler" ferme sans rien creer.
        # Une fois la facture enregistree, le dialogue reste ouvert et ce
        # bouton ne fait plus que le fermer (les donnees sont deja
        # persistees) : le libeller "Fermer" evite toute confusion.
        has_saved = bool(self._source_facture and self._source_facture.id is not None)
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(
            "Fermer" if has_saved else "Annuler"
        )

    def open_documents_folder(self) -> None:
        open_folder(self.service.exports_dir)

    def _refresh_source_facture(self) -> None:
        if self._source_facture is None or self._source_facture.id is None:
            return

        refreshed = self.service.get_facture(self._source_facture.id)
        if refreshed is not None:
            self._source_facture = refreshed
            self.facture = refreshed

        self._sync_document_buttons()

    def generate_docx(self) -> None:
        if self._source_facture is None or self._source_facture.id is None:
            QMessageBox.information(self, "Generation", "Enregistrez d'abord la facture.")
            return

        try:
            preview = self.service.preview(self._build_facture())
        except ValueError as exc:
            QMessageBox.warning(self, "Facture incomplete", str(exc))
            return

        response = QMessageBox.question(
            self,
            "Apercu avant generation",
            f"{preview}\n\nGenerer le document DOCX ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if response != QMessageBox.StandardButton.Yes:
            return

        try:
            self.service.generate_docx(self._source_facture.id)
        except Exception as exc:
            QMessageBox.warning(self, "Erreur", str(exc))
            return

        self._refresh_source_facture()
        notify_success(self, "Document DOCX genere.")

    def generate_pdf(self) -> None:
        if self._source_facture is None or self._source_facture.id is None:
            QMessageBox.information(self, "Export PDF", "Enregistrez d'abord la facture.")
            return

        facture_id = self._source_facture.id

        def on_success(_result: object) -> None:
            self._refresh_source_facture()
            notify_success(self, "Document PDF genere.")

        def on_error(exc: Exception) -> None:
            if isinstance(exc, PdfConversionTimeoutError):
                QMessageBox.warning(
                    self,
                    "Generation PDF",
                    "La generation du PDF semble bloquee.\n\n"
                    "Veuillez verifier qu'aucune fenetre Microsoft Word "
                    "n'attend votre intervention.",
                )
                return
            QMessageBox.warning(self, "Erreur", str(exc))

        run_task_with_progress(
            self,
            "Generation du PDF...\nVeuillez patienter.",
            lambda: self.service.generate_pdf(facture_id),
            on_success,
            on_error,
        )

    def open_docx(self) -> None:
        if self._source_facture is None or self._source_facture.id is None:
            QMessageBox.information(self, "Document", "Enregistrez d'abord la facture.")
            return

        try:
            self.service.open_document(self._source_facture.id)
        except FileNotFoundError as exc:
            QMessageBox.warning(self, "Document", str(exc))

    def open_pdf(self) -> None:
        if self._source_facture is None or self._source_facture.id is None:
            QMessageBox.information(self, "PDF", "Enregistrez d'abord la facture.")
            return

        try:
            self.service.open_pdf(self._source_facture.id)
        except FileNotFoundError as exc:
            QMessageBox.warning(self, "PDF", str(exc))

    # ===== Sauvegarde =====

    def save(self) -> None:
        facture = self._build_facture()

        try:
            self.service.preview(facture)
        except ValueError as exc:
            QMessageBox.warning(self, "Facture incomplete", str(exc))
            return

        is_new = facture.id is None

        try:
            if is_new:
                facture.id = self.service.create_facture(facture)
            else:
                self.service.update_facture(facture)
        except ValueError as exc:
            QMessageBox.warning(self, "Facture invalide", str(exc))
            return

        saved = self.service.get_facture(facture.id)
        if saved is not None:
            facture = saved

        self.facture = facture
        self._source_facture = facture

        # Le dialogue reste ouvert apres l'enregistrement : les documents
        # DOCX/PDF deviennent immediatement generables, sans repasser par la
        # liste (Sprint 12.0).
        self.setWindowTitle("Modifier une facture")
        self._sync_document_buttons()
        self._update_close_button()
        self._refresh_preview()

        notify_success(self, "Facture creee." if is_new else "Facture modifiee.")

    def show_preview(self) -> None:
        self._refresh_preview()
        self.tabs.setCurrentWidget(self.preview_text.parent())

    def _build_facture(self) -> Facture:
        source = self._source_facture
        # Base de repli pour tous les champs non exposes par un widget dans ce
        # dialogue : self.facture contient deja soit la facture en cours de
        # modification, soit l'instantane initial (ex. depuis une prestation
        # ou un contrat), soit une facture vierge - jamais None, jamais perdu
        # silencieusement.
        base = self.facture

        facture = Facture(
            id=source.id if source else None,
            facture_number=self.facture_number.text().strip(),
            formation_id=self.formation_combo.currentData(),
            organization_id=self.organization_combo.currentData(),
            prestation_id=(
                self._source_facture.prestation_id
                if self._source_facture
                else self._initial_prestation_id
            ),
            contract_id=(
                self._source_facture.contract_id
                if self._source_facture
                else self._initial_contract_id
            ),
            # Instantane Producteur : jamais saisi dans ce dialogue, jamais
            # recalcule ici. Une nouvelle facture le recoit du Producteur actif
            # dans FactureService.create_facture ; une facture existante
            # conserve tel quel l'instantane deja enregistre (meme principe
            # que Contrats et Devis).
            producteur_id=base.producteur_id,
            producteur_nom=base.producteur_nom,
            producteur_forme_juridique=base.producteur_forme_juridique,
            producteur_adresse=base.producteur_adresse,
            producteur_code_postal=base.producteur_code_postal,
            producteur_ville=base.producteur_ville,
            producteur_siret=base.producteur_siret,
            producteur_ape=base.producteur_ape,
            producteur_licence=base.producteur_licence,
            producteur_tva_intracommunautaire=base.producteur_tva_intracommunautaire,
            producteur_telephone=base.producteur_telephone,
            producteur_email=base.producteur_email,
            producteur_site=base.producteur_site,
            producteur_representant=base.producteur_representant,
            producteur_fonction=base.producteur_fonction,
            producteur_iban=base.producteur_iban,
            producteur_bic=base.producteur_bic,
            producteur_logo_path=base.producteur_logo_path,
            # Formation : instantane complet saisi depuis la fiche Formation
            # selectionnee (meme principe que le module Contrats).
            formation_nom=self.formation_nom.text().strip(),
            formation_adresse=self.formation_adresse.text().strip(),
            formation_postal_code=self.formation_postal_code.text().strip(),
            formation_city=self.formation_city.text().strip(),
            formation_phone=self.formation_phone.text().strip(),
            formation_email=self.formation_email.text().strip(),
            formation_site_internet=self.formation_site_internet.text().strip(),
            formation_siren=self.formation_siren.text().strip(),
            formation_siret=self.formation_siret.text().strip(),
            formation_ape=self.formation_ape.text().strip(),
            formation_licence=self.formation_licence.text().strip(),
            formation_iban=self.formation_iban.text().strip(),
            formation_bic=self.formation_bic.text().strip(),
            formation_social_number=self.formation_social_number.text().strip(),
            formation_notes=self.formation_notes.toPlainText().strip(),
            # Organisateur : idem, instantane complet.
            organisateur_structure=self.organisateur_nom.text().strip(),
            organisateur_forme=self.organisateur_forme.text().strip(),
            organisateur_adresse=self.organisateur_adresse.text().strip(),
            organisateur_postal_code=self.organisateur_postal_code.text().strip(),
            organisateur_city=self.organisateur_city.text().strip(),
            organisateur_siret=self.organisateur_siret.text().strip(),
            organisateur_phone=self.organisateur_phone.text().strip(),
            organisateur_email=self.organisateur_email.text().strip(),
            organisateur_site_internet=self.organisateur_site_internet.text().strip(),
            organisateur_ape=self.organisateur_ape.text().strip(),
            organisateur_licence=self.organisateur_licence.text().strip(),
            organisateur_tva=self.organisateur_tva.text().strip(),
            organisateur_representant=self.organisateur_representant.text().strip(),
            organisateur_fonction=self.organisateur_fonction.text().strip(),
            organisateur_iban=self.organisateur_iban.text().strip(),
            organisateur_bic=self.organisateur_bic.text().strip(),
            organisateur_notes=self.organisateur_notes.toPlainText().strip(),
            spectacle_nom=self.objet.text().strip(),
            spectacle_duree=base.spectacle_duree,
            prestation_date=self.date_prestation.date().toString("dd/MM/yyyy"),
            prestation_lieu=self.lieu.text().strip(),
            prestation_city=self.ville.text().strip(),
            prestation_adresse=base.prestation_adresse,
            prestation_postal_code=base.prestation_postal_code,
            prestation_convocation=base.prestation_convocation,
            prestation_horaire=base.prestation_horaire,
            montant=self.montant.value(),
            tva=self.tva.text().strip(),
            acompte=self.acompte.value(),
            total=self.total.value(),
            mode_paiement=self.mode.currentText(),
            echeance=self.echeance.text().strip(),
            observations=self.notes.toPlainText().strip(),
            comments=self.description.toPlainText().strip(),
            docx_path=source.docx_path if source else "",
            pdf_path=source.pdf_path if source else "",
            status=str(self.status.currentData() or "draft"),
            created_at=source.created_at if source else None,
            updated_at=source.updated_at if source else None,
            generated_at=source.generated_at if source else None,
        )
        return facture

    def _fill_form(self, facture: Facture) -> None:
        self.facture_number.setText(facture.facture_number or self.service.next_facture_number())

        formation_index = self.formation_combo.findData(facture.formation_id)
        self.formation_combo.setCurrentIndex(formation_index if formation_index >= 0 else 0)

        organization_index = self.organization_combo.findData(facture.organization_id)
        self.organization_combo.setCurrentIndex(organization_index if organization_index >= 0 else 0)

        self.formation_nom.setText(facture.formation_nom or "")
        self.formation_adresse.setText(facture.formation_adresse or "")
        self.formation_postal_code.setText(facture.formation_postal_code or "")
        self.formation_city.setText(facture.formation_city or "")
        self.formation_phone.setText(facture.formation_phone or "")
        self.formation_email.setText(facture.formation_email or "")
        self.formation_site_internet.setText(facture.formation_site_internet or "")
        self.formation_siren.setText(facture.formation_siren or "")
        self.formation_siret.setText(facture.formation_siret or "")
        self.formation_ape.setText(facture.formation_ape or "")
        self.formation_licence.setText(facture.formation_licence or "")
        self.formation_iban.setText(facture.formation_iban or "")
        self.formation_bic.setText(facture.formation_bic or "")
        self.formation_social_number.setText(facture.formation_social_number or "")
        self.formation_notes.setPlainText(facture.formation_notes or "")

        self.organisateur_nom.setText(facture.organisateur_structure or "")
        self.organisateur_forme.setText(facture.organisateur_forme or "")
        self.organisateur_adresse.setText(facture.organisateur_adresse or "")
        self.organisateur_postal_code.setText(facture.organisateur_postal_code or "")
        self.organisateur_city.setText(facture.organisateur_city or "")
        self.organisateur_siret.setText(facture.organisateur_siret or "")
        self.organisateur_phone.setText(facture.organisateur_phone or "")
        self.organisateur_email.setText(facture.organisateur_email or "")
        self.organisateur_site_internet.setText(facture.organisateur_site_internet or "")
        self.organisateur_ape.setText(facture.organisateur_ape or "")
        self.organisateur_licence.setText(facture.organisateur_licence or "")
        self.organisateur_tva.setText(facture.organisateur_tva or "")
        self.organisateur_representant.setText(facture.organisateur_representant or "")
        self.organisateur_fonction.setText(facture.organisateur_fonction or "")
        self.organisateur_iban.setText(facture.organisateur_iban or "")
        self.organisateur_bic.setText(facture.organisateur_bic or "")
        self.organisateur_notes.setPlainText(facture.organisateur_notes or "")

        self.objet.setText(facture.spectacle_nom or "")
        self.lieu.setText(facture.prestation_lieu or "")
        self.ville.setText(facture.prestation_city or "")
        self.description.setPlainText(facture.comments or "")

        self.montant.setValue(float(facture.montant or 0))
        self.tva.setText(facture.tva or "")
        self.acompte.setValue(float(facture.acompte or 0))
        self.echeance.setText(facture.echeance or "")
        self.notes.setPlainText(facture.observations or "")

        mode_index = self.mode.findText(facture.mode_paiement or "Virement")
        if mode_index >= 0:
            self.mode.setCurrentIndex(mode_index)

        status_index = self.status.findData(facture.status or "draft")
        if status_index >= 0:
            self.status.setCurrentIndex(status_index)

        date_text = facture.prestation_date
        if date_text:
            parsed = QDate.fromString(date_text, "dd/MM/yyyy")
            if parsed.isValid():
                self.date_prestation.setDate(parsed)
                self.date_general.setDate(parsed)
