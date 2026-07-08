from __future__ import annotations

from typing import Any

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)

from app.models.contract import Contract
from app.services.artist_service import ArtistService
from app.services.contract_service import ContractService
from app.services.organization_service import OrganizationService


class ContractDialog(QDialog):
    def __init__(
        self,
        parent: Any = None,
        contract: Contract | None = None,
        service: ContractService | None = None,
        artist_service: ArtistService | None = None,
        organization_service: OrganizationService | None = None,
    ) -> None:
        super().__init__(parent)

        self.service = service or ContractService()
        self.artist_service = artist_service or ArtistService()
        self.organization_service = organization_service or OrganizationService()
        self._source_contract = contract
        self.contract = contract or Contract(contract_number=self.service.next_contract_number())

        self.setWindowTitle("Modifier un contrat" if contract else "Nouveau contrat")
        self.resize(760, 800)

        layout = QVBoxLayout(self)

        artist_group = QGroupBox("Artiste")
        artist_form = QFormLayout(artist_group)

        organizer_group = QGroupBox("Organisateur")
        organizer_form = QFormLayout(organizer_group)

        performance_group = QGroupBox("Prestation")
        form = QFormLayout(performance_group)

        # ===== Artiste : selection + informations recuperees automatiquement =====

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

        artist_form.addRow("Artiste", self.artist_combo)
        artist_form.addRow("Nom", self.artiste_nom)
        artist_form.addRow("Adresse", self.artiste_adresse)
        artist_form.addRow("Code postal", self.artiste_postal_code)
        artist_form.addRow("Ville", self.artiste_city)
        artist_form.addRow("Telephone", self.artiste_phone)
        artist_form.addRow("Email", self.artiste_email)
        artist_form.addRow("SIREN", self.artiste_siren)
        artist_form.addRow("SIRET", self.artiste_siret)
        artist_form.addRow("Code APE", self.artiste_ape)
        artist_form.addRow("Licence", self.artiste_licence)
        artist_form.addRow("IBAN", self.artiste_iban)
        artist_form.addRow("BIC", self.artiste_bic)
        artist_form.addRow("Numero de securite sociale", self.artiste_social_number)
        artist_form.addRow("Notes", self.artiste_notes)

        # ===== Organisateur : selection + informations recuperees automatiquement =====

        self.organization_combo = QComboBox()
        self._reload_organization_choices()

        self.contract_number = QLineEdit()
        self.contract_number.setReadOnly(True)

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

        self.spectacle = QLineEdit()

        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())

        self.adresse = QLineEdit()
        self.convocation = QLineEdit()
        self.horaire = QLineEdit()
        self.duree = QLineEdit()

        self.montant = QDoubleSpinBox()
        self.montant.setMaximum(1000000)
        self.montant.setDecimals(2)
        self.montant.setSuffix(" EUR")

        self.mode = QComboBox()
        self.mode.addItems(["Virement", "Cheque"])

        self.status = QComboBox()
        self.status.addItem("Brouillon", "draft")
        self.status.addItem("Valide", "validated")
        self.status.addItem("Signe", "signed")

        self.hebergement = QCheckBox()
        self.restauration = QCheckBox()
        self.kilometrage = QCheckBox()
        self.comments = QTextEdit()
        self.comments.setFixedHeight(90)

        organizer_form.addRow("Organisateur", self.organization_combo)
        organizer_form.addRow("Numero", self.contract_number)
        organizer_form.addRow("Structure", self.organisateur)
        organizer_form.addRow("Forme juridique", self.organisateur_forme)
        organizer_form.addRow("Adresse", self.organisateur_adresse)
        organizer_form.addRow("Code postal", self.organisateur_postal_code)
        organizer_form.addRow("Ville", self.organisateur_city)
        organizer_form.addRow("SIRET", self.organisateur_siret)
        organizer_form.addRow("Telephone", self.organisateur_phone)
        organizer_form.addRow("Email", self.organisateur_email)
        organizer_form.addRow("Site internet", self.organisateur_site_internet)
        organizer_form.addRow("Code APE", self.organisateur_ape)
        organizer_form.addRow("Licence spectacle", self.organisateur_licence)
        organizer_form.addRow("TVA intracommunautaire", self.organisateur_tva)
        organizer_form.addRow("Representee par", self.organisateur_representant)
        organizer_form.addRow("Fonction", self.organisateur_fonction)
        organizer_form.addRow("IBAN", self.organisateur_iban)
        organizer_form.addRow("BIC", self.organisateur_bic)
        organizer_form.addRow("Notes", self.organisateur_notes)

        form.addRow("Spectacle", self.spectacle)
        form.addRow("Date", self.date)
        form.addRow("Adresse", self.adresse)
        form.addRow("Convocation", self.convocation)
        form.addRow("Horaire", self.horaire)
        form.addRow("Duree", self.duree)
        form.addRow("Montant (cachet)", self.montant)
        form.addRow("Mode paiement", self.mode)
        form.addRow("Statut", self.status)
        form.addRow("Hebergement", self.hebergement)
        form.addRow("Restauration", self.restauration)
        form.addRow("Kilometrage", self.kilometrage)
        form.addRow("Commentaires", self.comments)

        layout.addWidget(artist_group)
        layout.addWidget(organizer_group)
        layout.addWidget(performance_group)

        self.btn_preview = QPushButton("Apercu")
        self.btn_preview.clicked.connect(self.show_preview)
        layout.addWidget(self.btn_preview)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.save)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        self._fill_form(self.contract)

        # Connectes apres le remplissage initial : un changement manuel de
        # l'utilisateur declenche l'auto-remplissage, pas le chargement du formulaire.
        self.artist_combo.currentIndexChanged.connect(self._on_artist_selected)
        self.organization_combo.currentIndexChanged.connect(self._on_organization_selected)

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

        # Le cachet habituel devient la valeur par defaut, mais reste modifiable.
        self.montant.setValue(float(artist.fee or 0))

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

    def save(self) -> None:
        contract = self._build_contract()

        try:
            self.service.preview(contract)
        except ValueError as exc:
            QMessageBox.warning(self, "Contrat incomplet", str(exc))
            return

        self.contract = contract
        self.accept()

    def show_preview(self) -> None:
        try:
            preview = self.service.preview(self._build_contract())
        except ValueError as exc:
            QMessageBox.warning(self, "Contrat incomplet", str(exc))
            return

        QMessageBox.information(self, "Apercu du contrat", preview)

    def _build_contract(self) -> Contract:
        contract = Contract(
            id=self._source_contract.id if self._source_contract else None,
            contract_number=self.contract_number.text().strip(),
            artist_id=self.artist_combo.currentData(),
            organization_id=self.organization_combo.currentData(),
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
            prestation_adresse=self.adresse.text().strip(),
            prestation_convocation=self.convocation.text().strip(),
            prestation_horaire=self.horaire.text().strip(),
            spectacle_duree=self.duree.text().strip(),
            cession_montant=self.montant.value(),
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
        contract.venue = contract.prestation_adresse
        contract.event_date = contract.prestation_date
        contract.gross_salary = float(contract.cession_montant or 0)
        return contract

    def _fill_form(self, contract: Contract) -> None:
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

        self.contract_number.setText(contract.contract_number or self.service.next_contract_number())
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
        self.adresse.setText(contract.prestation_adresse or contract.venue or "")
        self.convocation.setText(contract.prestation_convocation or "")
        self.horaire.setText(contract.prestation_horaire or contract.start_time or "")
        self.duree.setText(contract.spectacle_duree or "")
        self.montant.setValue(float(contract.cession_montant or contract.gross_salary or 0))
        self.hebergement.setChecked(bool(contract.hebergement))
        self.restauration.setChecked(bool(contract.restauration))
        self.kilometrage.setChecked(bool(contract.kilometrage))
        self.comments.setPlainText(contract.comments or "")

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
