from __future__ import annotations

import webbrowser
from typing import Any

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from app.documents.placeholder_engine import PlaceholderEngine
from app.models.prestation import Prestation
from app.services.artist_service import ArtistService
from app.services.contract_service import ContractService
from app.services.devis_service import DevisService
from app.services.facture_service import FactureService
from app.services.organization_service import OrganizationService
from app.ui.theme import style_dialog_title, style_muted_text

INTERMIPAIE_URL = "https://intermipaie.fr/simulateur-paie-spectacle/"


class IntermiPaieDialog(QDialog):
    """Assistance vers le simulateur officiel IntermiPaie (calcul du salaire
    d'une prestation intermittente).

    YGNT Manager n'effectue et ne stocke jamais aucun calcul de paie : ce
    dialogue se contente de recapituler, en lecture seule, les informations
    déjà connues d'une prestation (aucune ecriture SQLite, aucun nouveau
    champ), pour aider l'utilisateur a les reporter sur
    https://intermipaie.fr - le seul moteur de simulation officiel.
    """

    def __init__(
        self,
        parent: Any,
        prestation: Prestation,
        artist_service: ArtistService | None = None,
        organization_service: OrganizationService | None = None,
        contract_service: ContractService | None = None,
        devis_service: DevisService | None = None,
        facture_service: FactureService | None = None,
    ) -> None:
        super().__init__(parent)

        self.artist_service = artist_service or ArtistService()
        self.organization_service = organization_service or OrganizationService()
        self.contract_service = contract_service or ContractService()
        self.devis_service = devis_service or DevisService()
        self.facture_service = facture_service or FactureService()

        self.setWindowTitle("Préparation du calcul de paie")
        self.setMinimumWidth(440)

        self._fields = self._collect_fields(prestation)

        layout = QVBoxLayout(self)

        title = QLabel("Préparation du calcul de paie")
        style_dialog_title(title)
        layout.addWidget(title)

        hint = QLabel(
            "Ces informations récapitulent la prestation pour preparer votre "
            "saisie sur le simulateur officiel IntermiPaie. YGNT Manager "
            "n'effectue et ne stocke aucun calcul de paie."
        )
        hint.setWordWrap(True)
        style_muted_text(hint)
        layout.addWidget(hint)

        form = QFormLayout()
        for label, value in self._fields:
            value_label = QLabel(value or "-")
            value_label.setWordWrap(True)
            form.addRow(f"{label} :", value_label)
        layout.addLayout(form)

        actions = QHBoxLayout()
        self.btn_open = QPushButton("🌐 Ouvrir IntermiPaie")
        self.btn_copy = QPushButton("📋 Copier les informations")
        self.btn_open.clicked.connect(self._open_intermipaie)
        self.btn_copy.clicked.connect(self._copy_to_clipboard)
        actions.addWidget(self.btn_open)
        actions.addWidget(self.btn_copy)
        layout.addLayout(actions)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText("Fermer")
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    # ===== Collecte des informations (lecture seule, services existants) =====

    def _collect_fields(self, prestation: Prestation) -> list[tuple[str, str]]:
        artist = (
            self.artist_service.get_artist(prestation.artist_id)
            if prestation.artist_id
            else None
        )
        organization = (
            self.organization_service.get_organization(prestation.organization_id)
            if prestation.organization_id
            else None
        )

        formation = (artist.stage_name or artist.legal_name or "") if artist else ""
        organisateur = organization.name if organization else ""
        montant = self._resolve_montant(prestation)

        return [
            ("Formation", formation),
            ("Organisateur", organisateur),
            ("Date", prestation.date_debut),
            ("Lieu", prestation.lieu_nom),
            ("Ville", prestation.lieu_city),
            ("Objet de la prestation", prestation.nom),
            ("Montant de la prestation", self._format_montant(montant)),
            ("Description", prestation.notes),
        ]

    def _resolve_montant(self, prestation: Prestation) -> float | None:
        """Le montant n'existe pas sur la Prestation elle-meme : on reutilise
        les services existants pour retrouver le premier montant connu parmi
        les documents déjà rattaches, par ordre de pertinence pour un calcul
        de salaire (le cachet artiste du Contrat, a defaut le montant du
        Devis, a defaut celui de la Facture). Purement indicatif : aucune
        valeur n'est jamais recalculee ni stockee."""
        if prestation.id is None:
            return None

        for contract in self.contract_service.list_for_prestation(prestation.id):
            amount = self._to_float(contract.cession_montant)
            if amount:
                return amount

        for devis in self.devis_service.list_for_prestation(prestation.id):
            amount = self._to_float(devis.montant)
            if amount:
                return amount

        for facture in self.facture_service.list_for_prestation(prestation.id):
            amount = self._to_float(facture.montant)
            if amount:
                return amount

        return None

    @staticmethod
    def _to_float(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _format_montant(montant: float | None) -> str:
        if montant is None:
            return ""
        return f"{PlaceholderEngine.FILTERS['currency'](montant)} €"

    # ===== Actions =====

    def _open_intermipaie(self) -> None:
        webbrowser.open(INTERMIPAIE_URL)

    def _copy_to_clipboard(self) -> None:
        QApplication.clipboard().setText(self._build_clipboard_text())

    def _build_clipboard_text(self) -> str:
        # Une section n'est incluse que si sa valeur est renseignee : jamais
        # de rubrique vide ("VILLE" sans rien dessous) dans le texte copie.
        sections = [
            f"{label.upper()}\n{value}"
            for label, value in self._fields
            if str(value or "").strip()
        ]
        return "\n\n".join(sections)
