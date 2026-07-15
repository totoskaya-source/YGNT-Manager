from __future__ import annotations

from typing import Any

from PySide6.QtCore import QDate, QSettings
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QScrollArea,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.models.paiement import Paiement
from app.services.facture_service import FactureService
from app.services.paiement_service import PaiementService
from app.ui.theme import style_date_edit

DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 850


class PaiementDialog(QDialog):
    def __init__(
        self,
        parent: Any = None,
        paiement: Paiement | None = None,
        service: PaiementService | None = None,
        facture_service: FactureService | None = None,
        initial_paiement: Paiement | None = None,
    ) -> None:
        super().__init__(parent)

        self.service = service or PaiementService()
        self.facture_service = facture_service or FactureService()
        self._source_paiement = paiement
        # initial_paiement permet de pre-remplir un NOUVEAU paiement (ex.
        # depuis une facture) sans basculer le dialogue en mode "modification".
        self.paiement = paiement or initial_paiement or Paiement(reference=self.service.next_paiement_number())

        self.setWindowTitle("Modifier un paiement" if paiement else "Nouveau paiement")
        self.setMinimumSize(900, 600)

        self._settings = QSettings("YGNTManager", "PaiementDialog")
        saved_geometry = self._settings.value("geometry")
        if saved_geometry is not None:
            self.restoreGeometry(saved_geometry)
        else:
            self.resize(DEFAULT_WIDTH, DEFAULT_HEIGHT)

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self._build_general_tab()
        self._build_facture_tab()
        self._build_paiement_tab()
        self._build_notes_tab()
        self._build_preview_tab()

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

        self._fill_form(self.paiement)
        self._refresh_preview()

        # Connecte apres le remplissage initial : un changement manuel de
        # l'utilisateur declenche l'auto-remplissage, pas le chargement du formulaire.
        self.facture_combo.currentIndexChanged.connect(self._on_facture_selected)
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

        self.reference = QLineEdit()
        self.reference.setReadOnly(True)

        self.date_paiement = QDateEdit()
        style_date_edit(self.date_paiement)
        self.date_paiement.setDate(QDate.currentDate())

        self.status = QComboBox()
        for code, label in PaiementService.STATUSES.items():
            self.status.addItem(label, code)

        form.addRow("Reference", self.reference)
        form.addRow("Date", self.date_paiement)
        form.addRow("Statut", self.status)

        self.tabs.addTab(self._wrap_in_scroll(content), "General")

    def _build_facture_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.facture_combo = QComboBox()
        self._reload_facture_choices()

        self.facture_reference = QLineEdit()
        self.facture_reference.setReadOnly(True)
        self.facture_organisateur = QLineEdit()
        self.facture_organisateur.setReadOnly(True)
        self.facture_montant = QLineEdit()
        self.facture_montant.setReadOnly(True)
        self.facture_deja_paye = QLineEdit()
        self.facture_deja_paye.setReadOnly(True)
        self.facture_reste_a_payer = QLineEdit()
        self.facture_reste_a_payer.setReadOnly(True)

        form.addRow("Facture", self.facture_combo)
        form.addRow("Reference", self.facture_reference)
        form.addRow("Organisateur", self.facture_organisateur)
        form.addRow("Montant facture", self.facture_montant)
        form.addRow("Deja paye", self.facture_deja_paye)
        form.addRow("Reste a payer", self.facture_reste_a_payer)

        self.tabs.addTab(self._wrap_in_scroll(content), "Facture")

    def _build_paiement_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.montant = QDoubleSpinBox()
        self.montant.setMaximum(1000000)
        self.montant.setDecimals(2)
        self.montant.setSuffix(" EUR")

        self.mode = QComboBox()
        self.mode.addItems(["Virement", "Cheque"])

        self.reference_bancaire = QLineEdit()

        form.addRow("Montant", self.montant)
        form.addRow("Mode de paiement", self.mode)
        form.addRow("Reference bancaire", self.reference_bancaire)

        self.tabs.addTab(self._wrap_in_scroll(content), "Paiement")

    def _build_notes_tab(self) -> None:
        content = QWidget()
        layout = QVBoxLayout(content)

        self.observations = QTextEdit()
        layout.addWidget(self.observations)

        self.tabs.addTab(content, "Notes")

    def _build_preview_tab(self) -> None:
        content = QWidget()
        layout = QVBoxLayout(content)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        layout.addWidget(self.preview_text)

        self.tabs.addTab(content, "Apercu")

    # ===== Liste deroulante Facture =====

    def _reload_facture_choices(self) -> None:
        self.facture_combo.addItem("(Selectionner une facture)", None)
        for facture in self.facture_service.list_factures():
            label = facture.facture_number or f"Facture #{facture.id}"
            self.facture_combo.addItem(label, facture.id)

    def _on_facture_selected(self, _index: int) -> None:
        facture_id = self.facture_combo.currentData()

        if facture_id is None:
            self._clear_facture_fields()
            return

        facture = self.facture_service.get_facture(facture_id)
        if facture is None:
            self._clear_facture_fields()
            return

        self.facture_reference.setText(facture.facture_number or "")
        self.facture_organisateur.setText(facture.organisateur_structure or "")
        self.facture_montant.setText(f"{float(facture.montant or 0):.2f} EUR")
        self.facture_deja_paye.setText(f"{self.service.total_paid(facture_id):.2f} EUR")
        self.facture_reste_a_payer.setText(f"{self.service.solde_restant(facture_id):.2f} EUR")

    def _clear_facture_fields(self) -> None:
        for field in (
            self.facture_reference,
            self.facture_organisateur,
            self.facture_montant,
            self.facture_deja_paye,
            self.facture_reste_a_payer,
        ):
            field.setText("")

    # ===== Onglet Apercu =====

    def _on_tab_changed(self, _index: int) -> None:
        if self.tabs.currentWidget() is self.preview_text.parent():
            self._refresh_preview()

    def _refresh_preview(self) -> None:
        try:
            text = self.service.preview(self._build_paiement())
        except ValueError as exc:
            text = f"Paiement incomplet : {exc}"
        self.preview_text.setPlainText(text)

    def _save_geometry(self) -> None:
        self._settings.setValue("geometry", self.saveGeometry())

    # ===== Sauvegarde =====

    def save(self) -> None:
        paiement = self._build_paiement()

        try:
            self.service.preview(paiement)
        except ValueError as exc:
            QMessageBox.warning(self, "Paiement incomplet", str(exc))
            return

        self.paiement = paiement
        self.accept()

    def _build_paiement(self) -> Paiement:
        source = self._source_paiement

        paiement = Paiement(
            id=source.id if source else None,
            reference=self.reference.text().strip(),
            facture_id=self.facture_combo.currentData(),
            date_paiement=self.date_paiement.date().toString("dd/MM/yyyy"),
            montant=self.montant.value(),
            mode_paiement=self.mode.currentText(),
            reference_bancaire=self.reference_bancaire.text().strip(),
            observations=self.observations.toPlainText().strip(),
            status=str(self.status.currentData() or "pending"),
            created_at=source.created_at if source else None,
            updated_at=source.updated_at if source else None,
        )
        return paiement

    def _fill_form(self, paiement: Paiement) -> None:
        self.reference.setText(paiement.reference or self.service.next_paiement_number())

        facture_index = self.facture_combo.findData(paiement.facture_id)
        self.facture_combo.setCurrentIndex(facture_index if facture_index >= 0 else 0)
        self._on_facture_selected(self.facture_combo.currentIndex())

        date_text = paiement.date_paiement
        if date_text:
            parsed = QDate.fromString(date_text, "dd/MM/yyyy")
            if parsed.isValid():
                self.date_paiement.setDate(parsed)

        status_index = self.status.findData(paiement.status or "pending")
        self.status.setCurrentIndex(status_index if status_index >= 0 else 0)

        self.montant.setValue(float(paiement.montant or 0))

        mode_index = self.mode.findText(paiement.mode_paiement or "Virement")
        if mode_index >= 0:
            self.mode.setCurrentIndex(mode_index)

        self.reference_bancaire.setText(paiement.reference_bancaire or "")
        self.observations.setPlainText(paiement.observations or "")
