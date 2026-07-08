from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
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

        self.setWindowTitle("Modifier un artiste" if artist else "Nouvel artiste")
        self.resize(520, 460)

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

        self.fee = QDoubleSpinBox()
        self.fee.setMaximum(100000)
        self.fee.setDecimals(2)
        self.fee.setSuffix(" EUR")

        self.email = QLineEdit()
        self.phone = QLineEdit()
        self.city = QLineEdit()
        self.notes = QTextEdit()
        self.notes.setFixedHeight(90)

        form.addRow("Nom legal", self.legal_name)
        form.addRow("Nom de scene", self.stage_name)
        form.addRow("Instrument", self.instrument)
        form.addRow("Statut", self.status)
        form.addRow("Cachet", self.fee)
        form.addRow("Email", self.email)
        form.addRow("Telephone", self.phone)
        form.addRow("Ville", self.city)
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
                "Artiste incomplet",
                "Renseignez au moins le nom legal ou le nom de scene.",
            )
            return

        self.artist = Artist(
            id=self._source_artist.id if self._source_artist else None,
            legal_name=self.legal_name.text().strip(),
            stage_name=self.stage_name.text().strip(),
            instrument=self.instrument.text().strip(),
            status=self.status.currentText(),
            fee=self.fee.value(),
            email=self.email.text().strip(),
            phone=self.phone.text().strip(),
            city=self.city.text().strip(),
            notes=self.notes.toPlainText().strip(),
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
        self.fee.setValue(float(artist.fee or 0))

        index = self.status.findText(artist.status)
        if index >= 0:
            self.status.setCurrentIndex(index)
