from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
)

from app.models.artist import Artist


class ArtistDialog(QDialog):
    def __init__(self, parent: Any = None, artist: Artist | None = None) -> None:
        super().__init__(parent)

        self._source_artist = artist
        self.artist: Artist | None = None

        self.setWindowTitle("Modifier une formation" if artist else "Nouvelle formation")
        self.resize(520, 620)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.legal_name = QLineEdit()
        self.stage_name = QLineEdit()
        self.instrument = QLineEdit()

        self.status = QComboBox()
        self.status.addItems([
            "Intermittent",
            "Salarie",
            "Auto-entrepreneur",
            "Autre",
        ])

        self.email = QLineEdit()
        self.phone = QLineEdit()
        self.city = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setFixedHeight(90)

        # Champs marketing/informatifs (Sprint 8.7) : jamais utilises dans un
        # devis, un contrat ou une facture.
        self.style_musical = QLineEdit()
        self.description = QTextEdit()
        self.description.setFixedHeight(70)
        self.logo_path = QLineEdit()
        self.photo_path = QLineEdit()
        self.site_internet = QLineEdit()
        self.facebook = QLineEdit()
        self.instagram = QLineEdit()
        self.youtube = QLineEdit()

        form.addRow("Nom legal", self.legal_name)
        form.addRow("Nom de scene", self.stage_name)
        form.addRow("Instrument", self.instrument)
        form.addRow("Statut", self.status)
        form.addRow("Email", self.email)
        form.addRow("Telephone", self.phone)
        form.addRow("Ville", self.city)
        form.addRow("Style musical", self.style_musical)
        form.addRow("Description", self.description)
        form.addRow("Logo (chemin du fichier)", self.logo_path)
        form.addRow("Photo principale (chemin du fichier)", self.photo_path)
        form.addRow("Site internet", self.site_internet)
        form.addRow("Facebook", self.facebook)
        form.addRow("Instagram", self.instagram)
        form.addRow("YouTube", self.youtube)
        form.addRow("Notes", self.notes)

        layout.addLayout(form)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.save)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        if artist is not None:
            self._fill_form(artist)

    def save(self) -> None:
        if not self.legal_name.text().strip() and not self.stage_name.text().strip():
            QMessageBox.warning(
                self,
                "Formation incomplete",
                "Renseignez au moins le nom legal ou le nom de scene.",
            )
            return

        self.artist = Artist(
            id=self._source_artist.id if self._source_artist else None,
            legal_name=self.legal_name.text().strip(),
            stage_name=self.stage_name.text().strip(),
            instrument=self.instrument.text().strip(),
            status=self.status.currentText(),
            # Cachet habituel retire de l'interface (Sprint 8.7) : la valeur
            # deja enregistree est conservee telle quelle, jamais resaisie.
            fee=self._source_artist.fee if self._source_artist else 0.0,
            email=self.email.text().strip(),
            phone=self.phone.text().strip(),
            city=self.city.text().strip(),
            notes=self.notes.toPlainText().strip(),
            style_musical=self.style_musical.text().strip(),
            description=self.description.toPlainText().strip(),
            logo_path=self.logo_path.text().strip(),
            photo_path=self.photo_path.text().strip(),
            site_internet=self.site_internet.text().strip(),
            facebook=self.facebook.text().strip(),
            instagram=self.instagram.text().strip(),
            youtube=self.youtube.text().strip(),
            created_at=self._source_artist.created_at if self._source_artist else None,
            updated_at=self._source_artist.updated_at if self._source_artist else None,
        )

        self.accept()

    def _fill_form(self, artist: Artist) -> None:
        self.legal_name.setText(artist.legal_name or "")
        self.stage_name.setText(artist.stage_name or "")
        self.instrument.setText(artist.instrument or "")
        self.email.setText(artist.email or "")
        self.phone.setText(artist.phone or "")
        self.city.setText(artist.city or "")
        self.notes.setPlainText(artist.notes or "")
        self.style_musical.setText(artist.style_musical or "")
        self.description.setPlainText(artist.description or "")
        self.logo_path.setText(artist.logo_path or "")
        self.photo_path.setText(artist.photo_path or "")
        self.site_internet.setText(artist.site_internet or "")
        self.facebook.setText(artist.facebook or "")
        self.instagram.setText(artist.instagram or "")
        self.youtube.setText(artist.youtube or "")

        index = self.status.findText(artist.status)
        if index >= 0:
            self.status.setCurrentIndex(index)
