from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QDate, QSettings
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
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
from app.models.contract import Contract
from app.services.artist_service import ArtistService
from app.services.contract_service import ContractService
from app.services.organization_service import OrganizationService
from app.ui.background_task import run_task_with_progress
from app.ui.dialogs import notify_success, open_folder

DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 850


class ContractDialog(QDialog):
    def __init__(
        self,
        parent: Any = None,
        contract: Contract | None = None,
        service: ContractService | None = None,
        artist_service: ArtistService | None = None,
        organization_service: OrganizationService | None = None,
        initial_contract: Contract | None = None,
    ) -> None:
        super().__init__(parent)

        self.service = service or ContractService()
        self.artist_service = artist_service or ArtistService()
        self.organization_service = organization_service or OrganizationService()
        self._source_contract = contract
        # initial_contract permet de pre-remplir un NOUVEAU contrat (ex. depuis une
        # prestation) sans basculer le dialogue en mode "modification".
        self._initial_prestation_id = initial_contract.prestation_id if initial_contract else None
        self.contract = contract or initial_contract or Contract(contract_number=self.service.next_contract_number())

        self.setWindowTitle("Modifier un contrat" if contract else "Nouveau contrat")
        self.setMinimumSize(900, 600)

        self._settings = QSettings("YGNTManager", "ContractDialog")
        saved_geometry = self._settings.value("geometry")
        if saved_geometry is not None:
            self.restoreGeometry(saved_geometry)
        else:
            self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)

        layout = QVBoxLayout(self)

        # Le numero de contrat reste visible quel que soit l'onglet actif.
        header = QHBoxLayout()
        header.addWidget(QLabel("Numero de contrat :"))
        self.contract_number = QLineEdit()
        self.contract_number.setReadOnly(True)
        self.contract_number.setMaximumWidth(200)
        header.addWidget(self.contract_number)
        header.addStretch()
        layout.addLayout(header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self._build_artist_tab()
        self._build_organizer_tab()
        self._build_performance_tab()
        self._build_financial_tab()
        self._build_preview_tab()

        # Actions document (DOCX/PDF) : disponibles uniquement une fois le
        # contrat enregistre (un identifiant est necessaire pour nommer/
        # retrouver les fichiers), meme ergonomie que Devis/Factures.
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

        self._fill_form(self.contract)

        if self._source_contract is None:
            # Nouveau contrat (eventuellement pre-rempli depuis une prestation) :
            # on derive les details complets depuis les fiches Artiste/Organisateur
            # liees. Pour un contrat existant, l'instantane deja enregistre est
            # conserve tel quel (jamais ecrase par les donnees actuelles des fiches).
            self._on_artist_selected(self.artist_combo.currentIndex())
            self._on_organization_selected(self.organization_combo.currentIndex())

        self._refresh_preview()
        self._sync_document_buttons()
        self._update_close_button()

        # Connectes apres le remplissage initial : un changement manuel de
        # l'utilisateur declenche l'auto-remplissage, pas le chargement du formulaire.
        self.artist_combo.currentIndexChanged.connect(self._on_artist_selected)
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

    def _build_artist_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.artist_combo = QComboBox()
        self._reload_artist_choices()

        self.artiste_nom = QLineEdit()
        self.artiste_adresse = QLineEdit()
        self.artiste_postal_code = QLineEdit()
        self.artiste_city = QLineEdit()
        self.artiste_phone = QLineEdit()
        self.artiste_email = QLineEdit()
        self.artiste_siren = QLineEdit()
        self.artiste_siret = QLineEdit()
        self.artiste_ape = QLineEdit()
        self.artiste_licence = QLineEdit()
        self.artiste_iban = QLineEdit()
        self.artiste_bic = QLineEdit()
        self.artiste_social_number = QLineEdit()
        self.artiste_notes = QTextEdit()
        self.artiste_notes.setFixedHeight(70)

        form.addRow("Artiste", self.artist_combo)
        form.addRow("Nom", self.artiste_nom)
        form.addRow("Adresse", self.artiste_adresse)
        form.addRow("Code postal", self.artiste_postal_code)
        form.addRow("Ville", self.artiste_city)
        form.addRow("Telephone", self.artiste_phone)
        form.addRow("Email", self.artiste_email)
        form.addRow("SIREN", self.artiste_siren)
        form.addRow("SIRET", self.artiste_siret)
        form.addRow("Code APE", self.artiste_ape)
        form.addRow("Licence", self.artiste_licence)
        form.addRow("IBAN", self.artiste_iban)
        form.addRow("BIC", self.artiste_bic)
        form.addRow("Numero de securite sociale", self.artiste_social_number)
        form.addRow("Notes", self.artiste_notes)

        self.tabs.addTab(self._wrap_in_scroll(content), "Artiste")

    def _build_organizer_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.organization_combo = QComboBox()
        self._reload_organization_choices()

        self.organisateur = QLineEdit()
        self.organisateur_forme = QLineEdit()
        self.organisateur_adresse = QLineEdit()
        self.organisateur_postal_code = QLineEdit()
        self.organisateur_city = QLineEdit()
        self.organisateur_siret = QLineEdit()
        self.organisateur_phone = QLineEdit()
        self.organisateur_email = QLineEdit()
        self.organisateur_ape = QLineEdit()
        self.organisateur_licence = QLineEdit()
        self.organisateur_tva = QLineEdit()
        self.organisateur_representant = QLineEdit()
        self.organisateur_fonction = QLineEdit()
        self.organisateur_site_internet = QLineEdit()
        self.organisateur_iban = QLineEdit()
        self.organisateur_bic = QLineEdit()
        self.organisateur_notes = QTextEdit()
        self.organisateur_notes.setFixedHeight(70)

        form.addRow("Organisateur", self.organization_combo)
        form.addRow("Structure", self.organisateur)
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

        self.spectacle = QLineEdit()

        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())

        self.convocation = QLineEdit()
        self.horaire = QLineEdit()
        self.lieu = QLineEdit()
        self.adresse = QLineEdit()
        self.postal_code = QLineEdit()
        self.city = QLineEdit()
        self.duree = QLineEdit()

        self.hebergement = QCheckBox()
        self.restauration = QCheckBox()
        self.kilometrage = QCheckBox()
        self.comments = QTextEdit()
        self.comments.setFixedHeight(90)

        self.status = QComboBox()
        self.status.addItem("Brouillon", "draft")
        self.status.addItem("Valide", "validated")
        self.status.addItem("Signe", "signed")

        form.addRow("Spectacle", self.spectacle)
        form.addRow("Date", self.date)
        form.addRow("Lieu (nom de la salle)", self.lieu)
        form.addRow("Adresse de la prestation", self.adresse)
        form.addRow("Code postal", self.postal_code)
        form.addRow("Ville", self.city)
        form.addRow("Duree", self.duree)
        form.addRow("Loges / convocation", self.convocation)
        form.addRow("Horaire de prestation", self.horaire)
        form.addRow("Hebergement", self.hebergement)
        form.addRow("Repas", self.restauration)
        form.addRow("Transport", self.kilometrage)
        form.addRow("Statut", self.status)
        form.addRow("Notes", self.comments)

        self.tabs.addTab(self._wrap_in_scroll(content), "Prestation")

    def _build_financial_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.montant = QDoubleSpinBox()
        self.montant.setMaximum(1000000)
        self.montant.setDecimals(2)
        self.montant.setSuffix(" EUR")

        self.acompte = QDoubleSpinBox()
        self.acompte.setMaximum(1000000)
        self.acompte.setDecimals(2)
        self.acompte.setSuffix(" EUR")

        self.cachet_tva = QLineEdit()
        self.cachet_tva.setPlaceholderText("Ex : 2,10% ou Exoneree")

        self.mode = QComboBox()
        self.mode.addItems(["Virement", "Cheque"])

        self.echeance = QLineEdit()
        self.echeance.setPlaceholderText("Ex : 30 jours apres la prestation")

        self.observations = QTextEdit()
        self.observations.setFixedHeight(90)

        form.addRow("Cachet", self.montant)
        form.addRow("Acompte", self.acompte)
        form.addRow("TVA", self.cachet_tva)
        form.addRow("Mode de paiement", self.mode)
        form.addRow("Echeance", self.echeance)
        form.addRow("Observations", self.observations)

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

    # ===== Listes deroulantes Artiste / Organisateur =====

    def _reload_artist_choices(self) -> None:
        self.artist_combo.addItem("(Aucun)", None)
        for artist in self.artist_service.list_artists():
            label = artist.stage_name or artist.legal_name or f"Artiste #{artist.id}"
            self.artist_combo.addItem(label, artist.id)

    def _reload_organization_choices(self) -> None:
        self.organization_combo.addItem("(Aucun / saisie libre)", None)
        for organization in self.organization_service.list_organizations():
            label = organization.name or f"Organisateur #{organization.id}"
            self.organization_combo.addItem(label, organization.id)

    def _on_artist_selected(self, _index: int) -> None:
        artist_id = self.artist_combo.currentData()
        if artist_id is None:
            return

        artist = self.artist_service.get_artist(artist_id)
        if artist is None:
            return

        self.artiste_nom.setText(artist.stage_name or artist.legal_name or "")
        self.artiste_adresse.setText(artist.address or "")
        self.artiste_postal_code.setText(artist.postal_code or "")
        self.artiste_city.setText(artist.city or "")
        self.artiste_phone.setText(artist.phone or "")
        self.artiste_email.setText(artist.email or "")
        self.artiste_siren.setText(artist.siren or "")
        self.artiste_siret.setText(artist.siret or "")
        self.artiste_ape.setText(artist.ape or "")
        self.artiste_licence.setText(artist.licence or "")
        self.artiste_iban.setText(artist.iban or "")
        self.artiste_bic.setText(artist.bic or "")
        self.artiste_social_number.setText(artist.social_number or "")
        self.artiste_notes.setPlainText(artist.notes or "")

        # Le montant n'est jamais pre-rempli depuis la Formation (Sprint 8.8) :
        # il reste toujours une saisie manuelle, par Prestation ou par Contrat.

    def _on_organization_selected(self, _index: int) -> None:
        organization_id = self.organization_combo.currentData()
        if organization_id is None:
            return

        organization = self.organization_service.get_organization(organization_id)
        if organization is None:
            return

        self.organisateur.setText(organization.name or "")
        self.organisateur_forme.setText(organization.legal_form or "")
        self.organisateur_adresse.setText(organization.address or "")
        self.organisateur_postal_code.setText(organization.postal_code or "")
        self.organisateur_city.setText(organization.city or "")
        self.organisateur_siret.setText(organization.siret or "")
        self.organisateur_phone.setText(organization.phone or "")
        self.organisateur_email.setText(organization.email or "")
        self.organisateur_ape.setText(organization.ape or "")
        self.organisateur_licence.setText(organization.licence or "")
        self.organisateur_tva.setText(organization.tva or "")
        self.organisateur_representant.setText(organization.president or "")
        self.organisateur_fonction.setText(organization.fonction or "")
        self.organisateur_site_internet.setText(organization.site_internet or "")
        self.organisateur_iban.setText(organization.iban or "")
        self.organisateur_bic.setText(organization.bic or "")
        self.organisateur_notes.setPlainText(organization.notes or "")

    # ===== Onglet Apercu =====

    def _on_tab_changed(self, _index: int) -> None:
        if self.tabs.currentWidget() is self.preview_text.parent():
            self._refresh_preview()

    def _refresh_preview(self) -> None:
        try:
            text = self.service.preview(self._build_contract())
        except ValueError as exc:
            text = f"Contrat incomplet : {exc}"
        self.preview_text.setPlainText(text)

    def _save_geometry(self) -> None:
        self._settings.setValue("geometry", self.saveGeometry())

    # ===== Generation / ouverture DOCX et PDF =====

    def _sync_document_buttons(self) -> None:
        has_saved_contract = bool(self._source_contract and self._source_contract.id is not None)
        self.btn_generate_docx.setEnabled(has_saved_contract)
        self.btn_generate_pdf.setEnabled(has_saved_contract)

        has_docx = bool(
            self._source_contract
            and self._source_contract.docx_path
            and Path(self._source_contract.docx_path).exists()
        )
        has_pdf = bool(
            self._source_contract
            and self._source_contract.pdf_path
            and Path(self._source_contract.pdf_path).exists()
        )
        self.btn_open_docx.setEnabled(has_docx)
        self.btn_open_pdf.setEnabled(has_pdf)

    def _update_close_button(self) -> None:
        # Tant que rien n'est enregistre, "Annuler" ferme sans rien creer.
        # Une fois le contrat enregistre, le dialogue reste ouvert et ce
        # bouton ne fait plus que le fermer (les donnees sont deja
        # persistees) : le libeller "Fermer" evite toute confusion.
        has_saved = bool(self._source_contract and self._source_contract.id is not None)
        self.buttons.button(QDialogButtonBox.StandardButton.Cancel).setText(
            "Fermer" if has_saved else "Annuler"
        )

    def open_documents_folder(self) -> None:
        open_folder(self.service.exports_dir)

    def _refresh_source_contract(self) -> None:
        if self._source_contract is None or self._source_contract.id is None:
            return

        refreshed = self.service.get_contract(self._source_contract.id)
        if refreshed is not None:
            self._source_contract = refreshed
            self.contract = refreshed

        self._sync_document_buttons()

    def generate_docx(self) -> None:
        if self._source_contract is None or self._source_contract.id is None:
            QMessageBox.information(self, "Generation", "Enregistrez d'abord le contrat.")
            return

        try:
            preview = self.service.preview(self._build_contract())
        except ValueError as exc:
            QMessageBox.warning(self, "Contrat incomplet", str(exc))
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
            self.service.generate_docx(self._source_contract.id)
        except Exception as exc:
            QMessageBox.warning(self, "Erreur", str(exc))
            return

        self._refresh_source_contract()
        notify_success(self, "Document DOCX genere.")

    def generate_pdf(self) -> None:
        if self._source_contract is None or self._source_contract.id is None:
            QMessageBox.information(self, "Export PDF", "Enregistrez d'abord le contrat.")
            return

        contract_id = self._source_contract.id

        def on_success(_result: object) -> None:
            self._refresh_source_contract()
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
            lambda: self.service.export_pdf(contract_id),
            on_success,
            on_error,
        )

    def open_docx(self) -> None:
        if self._source_contract is None or self._source_contract.id is None:
            QMessageBox.information(self, "Document", "Enregistrez d'abord le contrat.")
            return

        try:
            self.service.open_document(self._source_contract.id)
        except FileNotFoundError as exc:
            QMessageBox.warning(self, "Document", str(exc))

    def open_pdf(self) -> None:
        if self._source_contract is None or self._source_contract.id is None:
            QMessageBox.information(self, "PDF", "Enregistrez d'abord le contrat.")
            return

        try:
            self.service.open_pdf(self._source_contract.id)
        except FileNotFoundError as exc:
            QMessageBox.warning(self, "PDF", str(exc))

    # ===== Sauvegarde =====

    def save(self) -> None:
        contract = self._build_contract()

        try:
            self.service.preview(contract)
        except ValueError as exc:
            QMessageBox.warning(self, "Contrat incomplet", str(exc))
            return

        is_new = contract.id is None

        try:
            if is_new:
                contract.id = self.service.create_contract(contract)
            else:
                self.service.update_contract(contract)
        except ValueError as exc:
            QMessageBox.warning(self, "Contrat invalide", str(exc))
            return

        saved = self.service.get_contract(contract.id)
        if saved is not None:
            contract = saved

        self.contract = contract
        self._source_contract = contract

        # Le dialogue reste ouvert apres l'enregistrement : les documents
        # DOCX/PDF deviennent immediatement generables, sans repasser par la
        # liste (Sprint 12.0).
        self.setWindowTitle("Modifier un contrat")
        self._sync_document_buttons()
        self._update_close_button()
        self._refresh_preview()

        notify_success(self, "Contrat cree." if is_new else "Contrat modifie.")

    def show_preview(self) -> None:
        self._refresh_preview()
        self.tabs.setCurrentWidget(self.preview_text.parent())

    def _build_contract(self) -> Contract:
        contract = Contract(
            id=self._source_contract.id if self._source_contract else None,
            contract_number=self.contract_number.text().strip(),
            artist_id=self.artist_combo.currentData(),
            organization_id=self.organization_combo.currentData(),
            prestation_id=(
                self._source_contract.prestation_id
                if self._source_contract
                else self._initial_prestation_id
            ),
            # Instantane Producteur : jamais saisi dans ce dialogue, jamais
            # recalcule ici. Un nouveau contrat le recoit du Producteur actif
            # dans ContractService.create_contract ; un contrat existant
            # conserve tel quel l'instantane deja enregistre.
            producteur_id=self._source_contract.producteur_id if self._source_contract else None,
            producteur_nom=self._source_contract.producteur_nom if self._source_contract else "",
            producteur_forme_juridique=(
                self._source_contract.producteur_forme_juridique if self._source_contract else ""
            ),
            producteur_adresse=self._source_contract.producteur_adresse if self._source_contract else "",
            producteur_code_postal=(
                self._source_contract.producteur_code_postal if self._source_contract else ""
            ),
            producteur_ville=self._source_contract.producteur_ville if self._source_contract else "",
            producteur_siret=self._source_contract.producteur_siret if self._source_contract else "",
            producteur_ape=self._source_contract.producteur_ape if self._source_contract else "",
            producteur_licence=self._source_contract.producteur_licence if self._source_contract else "",
            producteur_tva_intracommunautaire=(
                self._source_contract.producteur_tva_intracommunautaire if self._source_contract else ""
            ),
            producteur_telephone=self._source_contract.producteur_telephone if self._source_contract else "",
            producteur_email=self._source_contract.producteur_email if self._source_contract else "",
            producteur_site=self._source_contract.producteur_site if self._source_contract else "",
            producteur_representant=(
                self._source_contract.producteur_representant if self._source_contract else ""
            ),
            producteur_fonction=self._source_contract.producteur_fonction if self._source_contract else "",
            producteur_iban=self._source_contract.producteur_iban if self._source_contract else "",
            producteur_bic=self._source_contract.producteur_bic if self._source_contract else "",
            artiste_nom=self.artiste_nom.text().strip(),
            artiste_adresse=self.artiste_adresse.text().strip(),
            artiste_postal_code=self.artiste_postal_code.text().strip(),
            artiste_city=self.artiste_city.text().strip(),
            artiste_phone=self.artiste_phone.text().strip(),
            artiste_email=self.artiste_email.text().strip(),
            artiste_siren=self.artiste_siren.text().strip(),
            artiste_siret=self.artiste_siret.text().strip(),
            artiste_ape=self.artiste_ape.text().strip(),
            artiste_licence=self.artiste_licence.text().strip(),
            artiste_iban=self.artiste_iban.text().strip(),
            artiste_bic=self.artiste_bic.text().strip(),
            artiste_social_number=self.artiste_social_number.text().strip(),
            artiste_notes=self.artiste_notes.toPlainText().strip(),
            organisateur_structure=self.organisateur.text().strip(),
            organisateur_forme=self.organisateur_forme.text().strip(),
            organisateur_adresse=self.organisateur_adresse.text().strip(),
            organisateur_postal_code=self.organisateur_postal_code.text().strip(),
            organisateur_city=self.organisateur_city.text().strip(),
            organisateur_siret=self.organisateur_siret.text().strip(),
            organisateur_phone=self.organisateur_phone.text().strip(),
            organisateur_email=self.organisateur_email.text().strip(),
            organisateur_ape=self.organisateur_ape.text().strip(),
            organisateur_licence=self.organisateur_licence.text().strip(),
            organisateur_tva=self.organisateur_tva.text().strip(),
            organisateur_representant=self.organisateur_representant.text().strip(),
            organisateur_fonction=self.organisateur_fonction.text().strip(),
            organisateur_site_internet=self.organisateur_site_internet.text().strip(),
            organisateur_iban=self.organisateur_iban.text().strip(),
            organisateur_bic=self.organisateur_bic.text().strip(),
            organisateur_notes=self.organisateur_notes.toPlainText().strip(),
            spectacle_nom=self.spectacle.text().strip(),
            prestation_date=self.date.date().toString("dd/MM/yyyy"),
            prestation_lieu=self.lieu.text().strip(),
            prestation_adresse=self.adresse.text().strip(),
            prestation_postal_code=self.postal_code.text().strip(),
            prestation_city=self.city.text().strip(),
            prestation_convocation=self.convocation.text().strip(),
            prestation_horaire=self.horaire.text().strip(),
            spectacle_duree=self.duree.text().strip(),
            cession_montant=self.montant.value(),
            acompte=self.acompte.value(),
            cachet_tva=self.cachet_tva.text().strip(),
            echeance=self.echeance.text().strip(),
            observations=self.observations.toPlainText().strip(),
            mode_paiement=self.mode.currentText(),
            status=str(self.status.currentData()),
            hebergement=self.hebergement.isChecked(),
            restauration=self.restauration.isChecked(),
            kilometrage=self.kilometrage.isChecked(),
            comments=self.comments.toPlainText().strip(),
            docx_path=self._source_contract.docx_path if self._source_contract else "",
            pdf_path=self._source_contract.pdf_path if self._source_contract else "",
            created_at=self._source_contract.created_at if self._source_contract else None,
            updated_at=self._source_contract.updated_at if self._source_contract else None,
            generated_at=self._source_contract.generated_at if self._source_contract else None,
        )
        contract.event_name = contract.spectacle_nom
        contract.venue = contract.prestation_lieu or contract.prestation_adresse
        contract.event_date = contract.prestation_date
        contract.gross_salary = float(contract.cession_montant or 0)
        return contract

    def _fill_form(self, contract: Contract) -> None:
        self.contract_number.setText(contract.contract_number or self.service.next_contract_number())

        artist_index = self.artist_combo.findData(contract.artist_id)
        self.artist_combo.setCurrentIndex(artist_index if artist_index >= 0 else 0)

        organization_index = self.organization_combo.findData(contract.organization_id)
        self.organization_combo.setCurrentIndex(organization_index if organization_index >= 0 else 0)

        self.artiste_nom.setText(contract.artiste_nom or "")
        self.artiste_adresse.setText(contract.artiste_adresse or "")
        self.artiste_postal_code.setText(contract.artiste_postal_code or "")
        self.artiste_city.setText(contract.artiste_city or "")
        self.artiste_phone.setText(contract.artiste_phone or "")
        self.artiste_email.setText(contract.artiste_email or "")
        self.artiste_siren.setText(contract.artiste_siren or "")
        self.artiste_siret.setText(contract.artiste_siret or "")
        self.artiste_ape.setText(contract.artiste_ape or "")
        self.artiste_licence.setText(contract.artiste_licence or "")
        self.artiste_iban.setText(contract.artiste_iban or "")
        self.artiste_bic.setText(contract.artiste_bic or "")
        self.artiste_social_number.setText(contract.artiste_social_number or "")
        self.artiste_notes.setPlainText(contract.artiste_notes or "")

        self.organisateur.setText(contract.organisateur_structure or "")
        self.organisateur_forme.setText(contract.organisateur_forme or "")
        self.organisateur_adresse.setText(contract.organisateur_adresse or "")
        self.organisateur_postal_code.setText(contract.organisateur_postal_code or "")
        self.organisateur_city.setText(contract.organisateur_city or "")
        self.organisateur_siret.setText(contract.organisateur_siret or "")
        self.organisateur_phone.setText(contract.organisateur_phone or "")
        self.organisateur_email.setText(contract.organisateur_email or "")
        self.organisateur_ape.setText(contract.organisateur_ape or "")
        self.organisateur_licence.setText(contract.organisateur_licence or "")
        self.organisateur_tva.setText(contract.organisateur_tva or "")
        self.organisateur_representant.setText(contract.organisateur_representant or "")
        self.organisateur_fonction.setText(contract.organisateur_fonction or "")
        self.organisateur_site_internet.setText(contract.organisateur_site_internet or "")
        self.organisateur_iban.setText(contract.organisateur_iban or "")
        self.organisateur_bic.setText(contract.organisateur_bic or "")
        self.organisateur_notes.setPlainText(contract.organisateur_notes or "")

        self.spectacle.setText(contract.spectacle_nom or contract.event_name or "")
        self.lieu.setText(contract.prestation_lieu or "")
        self.adresse.setText(contract.prestation_adresse or "")
        self.postal_code.setText(contract.prestation_postal_code or "")
        self.city.setText(contract.prestation_city or "")
        self.convocation.setText(contract.prestation_convocation or "")
        self.horaire.setText(contract.prestation_horaire or contract.start_time or "")
        self.duree.setText(contract.spectacle_duree or "")
        self.hebergement.setChecked(bool(contract.hebergement))
        self.restauration.setChecked(bool(contract.restauration))
        self.kilometrage.setChecked(bool(contract.kilometrage))
        self.comments.setPlainText(contract.comments or "")

        self.montant.setValue(float(contract.cession_montant or contract.gross_salary or 0))
        self.acompte.setValue(float(contract.acompte or 0))
        self.cachet_tva.setText(contract.cachet_tva or "")
        self.echeance.setText(contract.echeance or "")
        self.observations.setPlainText(contract.observations or "")

        mode_index = self.mode.findText(contract.mode_paiement or "Virement")
        if mode_index >= 0:
            self.mode.setCurrentIndex(mode_index)

        status_index = self.status.findData(contract.status or "draft")
        if status_index >= 0:
            self.status.setCurrentIndex(status_index)

        date_text = contract.prestation_date or contract.event_date
        if date_text:
            parsed = QDate.fromString(date_text, "dd/MM/yyyy")
            if parsed.isValid():
                self.date.setDate(parsed)
