from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models.organization import Organization


class OrganizationDialog(QDialog):
    def __init__(self, parent: Any = None, organization: Organization | None = None) -> None:
        super().__init__(parent)

        self._source_organization = organization
        self.organization: Organization | None = None

        self.setWindowTitle("Modifier un organisateur" if organization else "Nouvel organisateur")
        self.resize(560, 680)

        outer_layout = QVBoxLayout(self)

        content = QWidget()
        layout = QVBoxLayout(content)

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
        self.tva = QLineEdit()
        self.president = QLineEdit()
        self.fonction = QLineEdit()
        self.site_internet = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setFixedHeight(90)

        general_group = QGroupBox("Informations generales")
        general_form = QFormLayout(general_group)
        general_form.addRow("Nom", self.name)
        general_form.addRow("Forme juridique", self.legal_form)
        general_form.addRow("SIRET", self.siret)
        general_form.addRow("Code APE", self.ape)
        general_form.addRow("Licence", self.licence)
        general_form.addRow("TVA intracommunautaire", self.tva)
        layout.addWidget(general_group)

        contact_group = QGroupBox("Coordonnees")
        contact_form = QFormLayout(contact_group)
        contact_form.addRow("Adresse", self.address)
        contact_form.addRow("Code postal", self.postal_code)
        contact_form.addRow("Ville", self.city)
        contact_form.addRow("Email", self.email)
        contact_form.addRow("Telephone", self.phone)
        contact_form.addRow("Site internet", self.site_internet)
        layout.addWidget(contact_group)

        representant_group = QGroupBox("Representant et coordonnees bancaires")
        representant_form = QFormLayout(representant_group)
        representant_form.addRow("Represente par", self.president)
        representant_form.addRow("Fonction", self.fonction)
        representant_form.addRow("IBAN", self.iban)
        representant_form.addRow("BIC", self.bic)
        layout.addWidget(representant_group)

        notes_group = QGroupBox("Notes")
        notes_form = QFormLayout(notes_group)
        notes_form.addRow(self.notes)
        layout.addWidget(notes_group)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setWidget(content)
        outer_layout.addWidget(scroll)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.save)
        self.buttons.rejected.connect(self.reject)
        outer_layout.addWidget(self.buttons)

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
            tva=self.tva.text().strip(),
            president=self.president.text().strip(),
            fonction=self.fonction.text().strip(),
            site_internet=self.site_internet.text().strip(),
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
        self.tva.setText(organization.tva or "")
        self.president.setText(organization.president or "")
        self.fonction.setText(organization.fonction or "")
        self.site_internet.setText(organization.site_internet or "")
        self.notes.setPlainText(organization.notes or "")
