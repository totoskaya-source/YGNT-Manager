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
from app.services.contract_service import ContractService


class ContractDialog(QDialog):
    def __init__(
        self,
        parent: Any = None,
        contract: Contract | None = None,
        service: ContractService | None = None,
    ) -> None:
        super().__init__(parent)

        self.service = service or ContractService()
        self._source_contract = contract
        self.contract = contract or Contract(contract_number=self.service.next_contract_number())

        self.setWindowTitle("Modifier un contrat" if contract else "Nouveau contrat")
        self.resize(720, 680)

        layout = QVBoxLayout(self)
        organizer_group = QGroupBox("Organisateur")
        organizer_form = QFormLayout(organizer_group)

        performance_group = QGroupBox("Prestation")
        form = QFormLayout(performance_group)

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

        organizer_form.addRow("Numero", self.contract_number)
        organizer_form.addRow("Structure", self.organisateur)
        organizer_form.addRow("Forme juridique", self.organisateur_forme)
        organizer_form.addRow("Adresse", self.organisateur_adresse)
        organizer_form.addRow("Code postal", self.organisateur_postal_code)
        organizer_form.addRow("Ville", self.organisateur_city)
        organizer_form.addRow("SIRET", self.organisateur_siret)
        organizer_form.addRow("Telephone", self.organisateur_phone)
        organizer_form.addRow("Email", self.organisateur_email)
        organizer_form.addRow("Code APE", self.organisateur_ape)
        organizer_form.addRow("Licence spectacle", self.organisateur_licence)
        organizer_form.addRow("TVA intracommunautaire", self.organisateur_tva)
        organizer_form.addRow("Representee par", self.organisateur_representant)
        organizer_form.addRow("Fonction", self.organisateur_fonction)

        form.addRow("Spectacle", self.spectacle)
        form.addRow("Date", self.date)
        form.addRow("Adresse", self.adresse)
        form.addRow("Convocation", self.convocation)
        form.addRow("Horaire", self.horaire)
        form.addRow("Duree", self.duree)
        form.addRow("Montant", self.montant)
        form.addRow("Mode paiement", self.mode)
        form.addRow("Statut", self.status)
        form.addRow("Hebergement", self.hebergement)
        form.addRow("Restauration", self.restauration)
        form.addRow("Kilometrage", self.kilometrage)
        form.addRow("Commentaires", self.comments)

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
