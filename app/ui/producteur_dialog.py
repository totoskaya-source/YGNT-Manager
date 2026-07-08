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

from app.models.producteur import Producteur


class ProducteurDialog(QDialog):
    def __init__(self, parent: Any = None, producteur: Producteur | None = None) -> None:
        super().__init__(parent)

        self._source_producteur = producteur
        self.producteur: Producteur | None = None

        self.setWindowTitle("Modifier un producteur" if producteur else "Nouveau producteur")
        self.resize(520, 620)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.nom = QLineEdit()
        self.forme_juridique = QLineEdit()
        self.adresse = QLineEdit()
        self.postal_code = QLineEdit()
        self.city = QLineEdit()
        self.siret = QLineEdit()
        self.ape = QLineEdit()
        self.licence = QLineEdit()
        self.tva = QLineEdit()
        self.iban = QLineEdit()
        self.bic = QLineEdit()
        self.representant = QLineEdit()
        self.fonction = QLineEdit()
        self.logo_path = QLineEdit()
        self.site_internet = QLineEdit()
        self.email = QLineEdit()
        self.phone = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setFixedHeight(90)

        form.addRow("Nom", self.nom)
        form.addRow("Forme juridique", self.forme_juridique)
        form.addRow("Adresse", self.adresse)
        form.addRow("Code postal", self.postal_code)
        form.addRow("Ville", self.city)
        form.addRow("SIRET", self.siret)
        form.addRow("Code APE", self.ape)
        form.addRow("Licence", self.licence)
        form.addRow("TVA intracommunautaire", self.tva)
        form.addRow("IBAN", self.iban)
        form.addRow("BIC", self.bic)
        form.addRow("Represente par", self.representant)
        form.addRow("Fonction", self.fonction)
        form.addRow("Logo (chemin du fichier)", self.logo_path)
        form.addRow("Site internet", self.site_internet)
        form.addRow("Email", self.email)
        form.addRow("Telephone", self.phone)
        form.addRow("Notes", self.notes)

        layout.addLayout(form)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.save)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        if producteur is not None:
            self._fill_form(producteur)

    def save(self) -> None:
        if not self.nom.text().strip():
            QMessageBox.warning(
                self,
                "Producteur incomplet",
                "Renseignez au moins le nom du producteur.",
            )
            return

        self.producteur = Producteur(
            id=self._source_producteur.id if self._source_producteur else None,
            nom=self.nom.text().strip(),
            forme_juridique=self.forme_juridique.text().strip(),
            adresse=self.adresse.text().strip(),
            postal_code=self.postal_code.text().strip(),
            city=self.city.text().strip(),
            siret=self.siret.text().strip(),
            ape=self.ape.text().strip(),
            licence=self.licence.text().strip(),
            tva=self.tva.text().strip(),
            iban=self.iban.text().strip(),
            bic=self.bic.text().strip(),
            representant=self.representant.text().strip(),
            fonction=self.fonction.text().strip(),
            logo_path=self.logo_path.text().strip(),
            site_internet=self.site_internet.text().strip(),
            email=self.email.text().strip(),
            phone=self.phone.text().strip(),
            notes=self.notes.toPlainText().strip(),
            actif=self._source_producteur.actif if self._source_producteur else False,
            created_at=self._source_producteur.created_at if self._source_producteur else None,
        )

        self.accept()

    def _fill_form(self, producteur: Producteur) -> None:
        self.nom.setText(producteur.nom or "")
        self.forme_juridique.setText(producteur.forme_juridique or "")
        self.adresse.setText(producteur.adresse or "")
        self.postal_code.setText(producteur.postal_code or "")
        self.city.setText(producteur.city or "")
        self.siret.setText(producteur.siret or "")
        self.ape.setText(producteur.ape or "")
        self.licence.setText(producteur.licence or "")
        self.tva.setText(producteur.tva or "")
        self.iban.setText(producteur.iban or "")
        self.bic.setText(producteur.bic or "")
        self.representant.setText(producteur.representant or "")
        self.fonction.setText(producteur.fonction or "")
        self.logo_path.setText(producteur.logo_path or "")
        self.site_internet.setText(producteur.site_internet or "")
        self.email.setText(producteur.email or "")
        self.phone.setText(producteur.phone or "")
        self.notes.setPlainText(producteur.notes or "")
