from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)

from app.models.organization import Organization


class OrganizationDialog(QDialog):
    def __init__(self, parent: Any = None, organization: Organization | None = None) -> None:
        super().__init__(parent)

        self._source_organization = organization
        self.organization: Organization | None = None

        self.setWindowTitle("Modifier un organisateur" if organization else "Nouvel organisateur")
        self.resize(520, 560)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.name = QLineEdit()
        self.legal_form = QLineEdit()
        self.address = QLineEdit()
        self.postal_code = QLineEdit()
        self.city = QLineEdit()
        self.siret = QLineEdit()
        self.ape = QLineEdit()
        self.licence = QLineEdit()
        self.email = QLineEdit()
        self.phone = QLineEdit()
        self.iban = QLineEdit()
        self.bic = QLineEdit()
        self.president = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setFixedHeight(90)

        form.addRow("Nom", self.name)
        form.addRow("Forme juridique", self.legal_form)
        form.addRow("Adresse", self.address)
        form.addRow("Code postal", self.postal_code)
        form.addRow("Ville", self.city)
        form.addRow("SIRET", self.siret)
        form.addRow("Code APE", self.ape)
        form.addRow("Licence", self.licence)
        form.addRow("Email", self.email)
        form.addRow("Telephone", self.phone)
        form.addRow("IBAN", self.iban)
        form.addRow("BIC", self.bic)
        form.addRow("President", self.president)
        form.addRow("Notes", self.notes)

        layout.addLayout(form)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.save)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        if organization is not None:
            self._fill_form(organization)

    def save(self) -> None:
        if not self.name.text().strip():
            QMessageBox.warning(
                self,
                "Organisateur incomplet",
                "Renseignez au moins le nom de l'organisateur.",
            )
            return

        self.organization = Organization(
            id=self._source_organization.id if self._source_organization else None,
            name=self.name.text().strip(),
            legal_form=self.legal_form.text().strip(),
            address=self.address.text().strip(),
            postal_code=self.postal_code.text().strip(),
            city=self.city.text().strip(),
            siret=self.siret.text().strip(),
            ape=self.ape.text().strip(),
            licence=self.licence.text().strip(),
            email=self.email.text().strip(),
            phone=self.phone.text().strip(),
            iban=self.iban.text().strip(),
            bic=self.bic.text().strip(),
            president=self.president.text().strip(),
            notes=self.notes.toPlainText().strip(),
            created_at=self._source_organization.created_at if self._source_organization else None,
        )

        self.accept()

    def _fill_form(self, organization: Organization) -> None:
        self.name.setText(organization.name or "")
        self.legal_form.setText(organization.legal_form or "")
        self.address.setText(organization.address or "")
        self.postal_code.setText(organization.postal_code or "")
        self.city.setText(organization.city or "")
        self.siret.setText(organization.siret or "")
        self.ape.setText(organization.ape or "")
        self.licence.setText(organization.licence or "")
        self.email.setText(organization.email or "")
        self.phone.setText(organization.phone or "")
        self.iban.setText(organization.iban or "")
        self.bic.setText(organization.bic or "")
        self.president.setText(organization.president or "")
        self.notes.setPlainText(organization.notes or "")
