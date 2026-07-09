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

from app.models.devis import Devis
from app.services.artist_service import ArtistService
from app.services.devis_service import DevisService
from app.services.organization_service import OrganizationService

DEFAULT_WIDTH = 1200
DEFAULT_HEIGHT = 850


class DevisDialog(QDialog):
    def __init__(
        self,
        parent: Any = None,
        devis: Devis | None = None,
        service: DevisService | None = None,
        artist_service: ArtistService | None = None,
        organization_service: OrganizationService | None = None,
    ) -> None:
        super().__init__(parent)

        self.service = service or DevisService()
        self.artist_service = artist_service or ArtistService()
        self.organization_service = organization_service or OrganizationService()
        self._source_devis = devis
        self.devis = devis or Devis(devis_number=self.service.next_devis_number())

        self.setWindowTitle("Modifier un devis" if devis else "Nouveau devis")
        self.setMinimumSize(900, 600)

        self._settings = QSettings("YGNTManager", "DevisDialog")
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

        self._fill_form(self.devis)

        if self._source_devis is None:
            # Nouveau devis : on derive les details depuis les fiches Formation
            # et Organisateur liees. Pour un devis existant, l'instantane deja
            # enregistre est conserve tel quel (jamais ecrase par les donnees
            # actuelles des fiches) - meme principe que pour les Contrats.
            self._on_formation_selected(self.formation_combo.currentIndex())
            self._on_organization_selected(self.organization_combo.currentIndex())

        self._refresh_preview()

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

        self.devis_number = QLineEdit()
        self.devis_number.setReadOnly(True)

        self.date_general = QDateEdit()
        self.date_general.setCalendarPopup(True)
        self.date_general.setDate(QDate.currentDate())

        self.date_validite = QDateEdit()
        self.date_validite.setCalendarPopup(True)
        self.date_validite.setDate(QDate.currentDate())

        self.status = QComboBox()
        for code, label in DevisService.STATUSES.items():
            self.status.addItem(label, code)

        form.addRow("Reference", self.devis_number)
        form.addRow("Date", self.date_general)
        form.addRow("Date de validite", self.date_validite)
        form.addRow("Statut", self.status)

        self.tabs.addTab(self._wrap_in_scroll(content), "General")

    def _build_formation_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.formation_combo = QComboBox()
        self._reload_formation_choices()

        self.formation_nom = QLineEdit()
        self.formation_nom.setReadOnly(True)
        self.formation_phone = QLineEdit()
        self.formation_phone.setReadOnly(True)
        self.formation_email = QLineEdit()
        self.formation_email.setReadOnly(True)
        self.formation_site_internet = QLineEdit()
        self.formation_site_internet.setReadOnly(True)

        form.addRow("Formation", self.formation_combo)
        form.addRow("Nom", self.formation_nom)
        form.addRow("Telephone", self.formation_phone)
        form.addRow("Email", self.formation_email)
        form.addRow("Site internet", self.formation_site_internet)

        self.tabs.addTab(self._wrap_in_scroll(content), "Formation")

    def _build_organizer_tab(self) -> None:
        content = QWidget()
        form = QFormLayout(content)

        self.organization_combo = QComboBox()
        self._reload_organization_choices()

        self.organisateur_nom = QLineEdit()
        self.organisateur_nom.setReadOnly(True)
        self.organisateur_phone = QLineEdit()
        self.organisateur_phone.setReadOnly(True)
        self.organisateur_email = QLineEdit()
        self.organisateur_email.setReadOnly(True)
        self.organisateur_adresse = QLineEdit()
        self.organisateur_adresse.setReadOnly(True)

        form.addRow("Organisateur", self.organization_combo)
        form.addRow("Nom", self.organisateur_nom)
        form.addRow("Telephone", self.organisateur_phone)
        form.addRow("Email", self.organisateur_email)
        form.addRow("Adresse", self.organisateur_adresse)

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
        self.duree = QLineEdit()

        form.addRow("Objet", self.objet)
        form.addRow("Date", self.date_prestation)
        form.addRow("Lieu", self.lieu)
        form.addRow("Ville", self.ville)
        form.addRow("Duree", self.duree)

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

        self.mode = QComboBox()
        self.mode.addItems(["Virement", "Cheque"])

        self.echeance = QLineEdit()
        self.echeance.setPlaceholderText("Ex : 30 jours apres la prestation")

        self.notes = QTextEdit()
        self.notes.setFixedHeight(90)

        form.addRow("Montant", self.montant)
        form.addRow("TVA", self.tva)
        form.addRow("Acompte", self.acompte)
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
        self.formation_phone.setText(artist.phone or "")
        self.formation_email.setText(artist.email or "")
        self.formation_site_internet.setText(artist.site_internet or "")

    def _on_organization_selected(self, _index: int) -> None:
        organization_id = self.organization_combo.currentData()
        if organization_id is None:
            return

        organization = self.organization_service.get_organization(organization_id)
        if organization is None:
            return

        self.organisateur_nom.setText(organization.name or "")
        self.organisateur_phone.setText(organization.phone or "")
        self.organisateur_email.setText(organization.email or "")
        self.organisateur_adresse.setText(organization.address or "")

    # ===== Onglet Apercu =====

    def _on_tab_changed(self, _index: int) -> None:
        if self.tabs.currentWidget() is self.preview_text.parent():
            self._refresh_preview()

    def _refresh_preview(self) -> None:
        try:
            text = self.service.preview(self._build_devis())
        except ValueError as exc:
            text = f"Devis incomplet : {exc}"
        self.preview_text.setPlainText(text)

    def _save_geometry(self) -> None:
        self._settings.setValue("geometry", self.saveGeometry())

    # ===== Sauvegarde =====

    def save(self) -> None:
        devis = self._build_devis()

        try:
            self.service.preview(devis)
        except ValueError as exc:
            QMessageBox.warning(self, "Devis incomplet", str(exc))
            return

        self.devis = devis
        self.accept()

    def show_preview(self) -> None:
        self._refresh_preview()
        self.tabs.setCurrentWidget(self.preview_text.parent())

    def _build_devis(self) -> Devis:
        source = self._source_devis

        devis = Devis(
            id=source.id if source else None,
            devis_number=self.devis_number.text().strip(),
            formation_id=self.formation_combo.currentData(),
            organization_id=self.organization_combo.currentData(),
            prestation_id=source.prestation_id if source else None,
            # Instantane Producteur : jamais saisi dans ce dialogue, jamais
            # recalcule ici. Un nouveau devis le recoit du Producteur actif
            # dans DevisService.create_devis ; un devis existant conserve tel
            # quel l'instantane deja enregistre (meme principe que Contrats).
            producteur_id=source.producteur_id if source else None,
            producteur_nom=source.producteur_nom if source else "",
            producteur_forme_juridique=source.producteur_forme_juridique if source else "",
            producteur_adresse=source.producteur_adresse if source else "",
            producteur_code_postal=source.producteur_code_postal if source else "",
            producteur_ville=source.producteur_ville if source else "",
            producteur_siret=source.producteur_siret if source else "",
            producteur_ape=source.producteur_ape if source else "",
            producteur_licence=source.producteur_licence if source else "",
            producteur_tva_intracommunautaire=source.producteur_tva_intracommunautaire if source else "",
            producteur_telephone=source.producteur_telephone if source else "",
            producteur_email=source.producteur_email if source else "",
            producteur_site=source.producteur_site if source else "",
            producteur_representant=source.producteur_representant if source else "",
            producteur_fonction=source.producteur_fonction if source else "",
            producteur_iban=source.producteur_iban if source else "",
            producteur_bic=source.producteur_bic if source else "",
            # Formation : les 4 champs affiches dans ce dialogue sont saisis
            # depuis la fiche Formation selectionnee ; les autres champs de
            # l'instantane (non exposes ici) sont conserves tels quels.
            formation_nom=self.formation_nom.text().strip(),
            formation_phone=self.formation_phone.text().strip(),
            formation_email=self.formation_email.text().strip(),
            formation_site_internet=self.formation_site_internet.text().strip(),
            formation_adresse=source.formation_adresse if source else "",
            formation_postal_code=source.formation_postal_code if source else "",
            formation_city=source.formation_city if source else "",
            formation_siren=source.formation_siren if source else "",
            formation_siret=source.formation_siret if source else "",
            formation_ape=source.formation_ape if source else "",
            formation_licence=source.formation_licence if source else "",
            formation_iban=source.formation_iban if source else "",
            formation_bic=source.formation_bic if source else "",
            formation_social_number=source.formation_social_number if source else "",
            formation_notes=source.formation_notes if source else "",
            # Organisateur : idem, seuls les 4 champs affiches sont saisis ici.
            organisateur_structure=self.organisateur_nom.text().strip(),
            organisateur_phone=self.organisateur_phone.text().strip(),
            organisateur_email=self.organisateur_email.text().strip(),
            organisateur_adresse=self.organisateur_adresse.text().strip(),
            organisateur_forme=source.organisateur_forme if source else "",
            organisateur_postal_code=source.organisateur_postal_code if source else "",
            organisateur_city=source.organisateur_city if source else "",
            organisateur_siret=source.organisateur_siret if source else "",
            organisateur_ape=source.organisateur_ape if source else "",
            organisateur_licence=source.organisateur_licence if source else "",
            organisateur_tva=source.organisateur_tva if source else "",
            organisateur_representant=source.organisateur_representant if source else "",
            organisateur_fonction=source.organisateur_fonction if source else "",
            organisateur_iban=source.organisateur_iban if source else "",
            organisateur_bic=source.organisateur_bic if source else "",
            organisateur_site_internet=source.organisateur_site_internet if source else "",
            organisateur_notes=source.organisateur_notes if source else "",
            spectacle_nom=self.objet.text().strip(),
            spectacle_duree=self.duree.text().strip(),
            prestation_date=self.date_prestation.date().toString("dd/MM/yyyy"),
            prestation_lieu=self.lieu.text().strip(),
            prestation_city=self.ville.text().strip(),
            prestation_adresse=source.prestation_adresse if source else "",
            prestation_postal_code=source.prestation_postal_code if source else "",
            prestation_convocation=source.prestation_convocation if source else "",
            prestation_horaire=source.prestation_horaire if source else "",
            montant=self.montant.value(),
            acompte=self.acompte.value(),
            tva=self.tva.text().strip(),
            mode_paiement=self.mode.currentText(),
            echeance=self.echeance.text().strip(),
            date_validite=self.date_validite.date().toString("dd/MM/yyyy"),
            observations=self.notes.toPlainText().strip(),
            comments=source.comments if source else "",
            hebergement=bool(source.hebergement) if source else False,
            restauration=bool(source.restauration) if source else False,
            kilometrage=bool(source.kilometrage) if source else False,
            docx_path=source.docx_path if source else "",
            pdf_path=source.pdf_path if source else "",
            status=str(self.status.currentData() or "draft"),
            created_at=source.created_at if source else None,
            updated_at=source.updated_at if source else None,
            generated_at=source.generated_at if source else None,
        )
        return devis

    def _fill_form(self, devis: Devis) -> None:
        self.devis_number.setText(devis.devis_number or self.service.next_devis_number())

        formation_index = self.formation_combo.findData(devis.formation_id)
        self.formation_combo.setCurrentIndex(formation_index if formation_index >= 0 else 0)

        organization_index = self.organization_combo.findData(devis.organization_id)
        self.organization_combo.setCurrentIndex(organization_index if organization_index >= 0 else 0)

        self.formation_nom.setText(devis.formation_nom or "")
        self.formation_phone.setText(devis.formation_phone or "")
        self.formation_email.setText(devis.formation_email or "")
        self.formation_site_internet.setText(devis.formation_site_internet or "")

        self.organisateur_nom.setText(devis.organisateur_structure or "")
        self.organisateur_phone.setText(devis.organisateur_phone or "")
        self.organisateur_email.setText(devis.organisateur_email or "")
        self.organisateur_adresse.setText(devis.organisateur_adresse or "")

        self.objet.setText(devis.spectacle_nom or "")
        self.lieu.setText(devis.prestation_lieu or "")
        self.ville.setText(devis.prestation_city or "")
        self.duree.setText(devis.spectacle_duree or "")

        self.montant.setValue(float(devis.montant or 0))
        self.tva.setText(devis.tva or "")
        self.acompte.setValue(float(devis.acompte or 0))
        self.echeance.setText(devis.echeance or "")
        self.notes.setPlainText(devis.observations or "")

        mode_index = self.mode.findText(devis.mode_paiement or "Virement")
        if mode_index >= 0:
            self.mode.setCurrentIndex(mode_index)

        status_index = self.status.findData(devis.status or "draft")
        if status_index >= 0:
            self.status.setCurrentIndex(status_index)

        date_text = devis.prestation_date
        if date_text:
            parsed = QDate.fromString(date_text, "dd/MM/yyyy")
            if parsed.isValid():
                self.date_prestation.setDate(parsed)
                self.date_general.setDate(parsed)

        validite_text = devis.date_validite
        if validite_text:
            parsed_validite = QDate.fromString(validite_text, "dd/MM/yyyy")
            if parsed_validite.isValid():
                self.date_validite.setDate(parsed_validite)
