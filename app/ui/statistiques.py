from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.services import stats_helper
from app.services.contract_service import ContractService
from app.services.devis_service import DevisService
from app.services.facture_service import FactureService
from app.services.organization_service import OrganizationService
from app.services.paiement_service import PaiementService
from app.services.prestation_service import PrestationService
from app.ui.theme import style_muted_text, style_page_title, style_stat_label, style_stat_value

ACTIVITY_LABELS = ("Prestations", "Devis", "Contrats", "Factures", "Paiements")
BILLING_LABELS = ("CA facture", "CA encaisse", "Montant restant a encaisser")
FACTURE_STATUS_LABELS = (
    ("paid", "Payees"),
    ("partial", "Partielles"),
    ("pending", "En attente"),
    ("cancelled", "Annulees"),
)
DEVIS_STATUS_LABELS = (
    ("draft", "Brouillon"),
    ("sent", "Envoyes"),
    ("accepted", "Acceptes"),
    ("refused", "Refuses"),
    ("expired", "Expires"),
)


class StatistiquesPage(QWidget):
    """Page Statistiques : vision chiffree de l'activite, en cartes
    uniquement (aucun graphique, aucune dependance externe).

    Toutes les valeurs proviennent des Services existants, une seule
    requete par module et par rafraichissement. Les calculs partages avec
    le Dashboard (CA, comptes, prochaines prestations) vivent dans
    app/services/stats_helper.py : jamais recalcules deux fois."""

    def __init__(
        self,
        prestation_service: PrestationService | None = None,
        devis_service: DevisService | None = None,
        contract_service: ContractService | None = None,
        facture_service: FactureService | None = None,
        paiement_service: PaiementService | None = None,
        organization_service: OrganizationService | None = None,
    ) -> None:
        super().__init__()

        self.prestation_service = prestation_service or PrestationService()
        self.devis_service = devis_service or DevisService()
        self.contract_service = contract_service or ContractService()
        self.facture_service = facture_service or FactureService()
        self.paiement_service = paiement_service or PaiementService(facture_service=self.facture_service)
        self.organization_service = organization_service or OrganizationService()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        outer.addWidget(scroll)

        content = QWidget()
        scroll.setWidget(content)

        layout = QVBoxLayout(content)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        title = QLabel("Statistiques")
        style_page_title(title)
        layout.addWidget(title)

        activity_card, self.activity_tiles = self._build_stats_card("Activite", ACTIVITY_LABELS)
        layout.addWidget(activity_card)

        billing_card, self.billing_tiles = self._build_stats_card("Chiffre d'affaires", BILLING_LABELS)
        layout.addWidget(billing_card)

        facture_status_card, self.facture_status_tiles = self._build_stats_card(
            "Facturation", [label for _code, label in FACTURE_STATUS_LABELS]
        )
        layout.addWidget(facture_status_card)

        devis_status_card, self.devis_status_tiles = self._build_stats_card(
            "Devis", [label for _code, label in DEVIS_STATUS_LABELS]
        )
        layout.addWidget(devis_status_card)

        top_organisateurs_card, self.top_organisateurs_layout = self._build_card("Top organisateurs")
        layout.addWidget(top_organisateurs_card)

        next_prestations_card, self.next_prestations_layout = self._build_card("Prochaines prestations")
        layout.addWidget(next_prestations_card)

        layout.addStretch()

        self.refresh()

    # ===== Construction des cartes =====

    @staticmethod
    def _build_card(title: str) -> tuple[QGroupBox, QVBoxLayout]:
        card = QGroupBox(title)
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        return card, layout

    def _build_stats_card(self, title: str, labels: Any) -> tuple[QGroupBox, dict[str, QLabel]]:
        card, layout = self._build_card(title)

        grid = QGridLayout()
        grid.setHorizontalSpacing(32)
        grid.setVerticalSpacing(4)
        tiles: dict[str, QLabel] = {}

        for column, label_text in enumerate(labels):
            value_label = QLabel("0")
            style_stat_value(value_label)

            caption_label = QLabel(label_text)
            style_stat_label(caption_label)

            grid.addWidget(value_label, 0, column)
            grid.addWidget(caption_label, 1, column)
            tiles[label_text] = value_label

        layout.addLayout(grid)
        return card, tiles

    # ===== Rafraichissement =====

    def refresh(self) -> None:
        # Une seule requete par module, comme le Dashboard : toutes les
        # sections ci-dessous reutilisent ces memes listes.
        prestations = self.prestation_service.list_prestations()
        devis_list = self.devis_service.list_devis()
        contracts = self.contract_service.list_contracts()
        factures = self.facture_service.list_factures()
        paiements = self.paiement_service.list_paiements()
        organizations = self.organization_service.list_organizations()

        self._refresh_activity(prestations, devis_list, contracts, factures, paiements)
        self._refresh_billing(factures, paiements)
        self._refresh_facture_status(factures)
        self._refresh_devis_status(devis_list)
        self._refresh_top_organisateurs(prestations, organizations)
        self._refresh_next_prestations(prestations)

    def _refresh_activity(
        self,
        prestations: list[Any],
        devis_list: list[Any],
        contracts: list[Any],
        factures: list[Any],
        paiements: list[Any],
    ) -> None:
        self.activity_tiles["Prestations"].setText(str(len(prestations)))
        self.activity_tiles["Devis"].setText(str(len(devis_list)))
        self.activity_tiles["Contrats"].setText(str(len(contracts)))
        self.activity_tiles["Factures"].setText(str(len(factures)))
        self.activity_tiles["Paiements"].setText(str(len(paiements)))

    def _refresh_billing(self, factures: list[Any], paiements: list[Any]) -> None:
        self.billing_tiles["CA facture"].setText(f"{stats_helper.ca_facture(factures):.2f} EUR")
        self.billing_tiles["CA encaisse"].setText(f"{stats_helper.ca_encaisse(paiements):.2f} EUR")
        self.billing_tiles["Montant restant a encaisser"].setText(
            f"{stats_helper.montant_restant_a_encaisser(factures, paiements):.2f} EUR"
        )

    def _refresh_facture_status(self, factures: list[Any]) -> None:
        counts = stats_helper.count_factures_by_status(factures)
        for code, label in FACTURE_STATUS_LABELS:
            self.facture_status_tiles[label].setText(str(counts[code]))

    def _refresh_devis_status(self, devis_list: list[Any]) -> None:
        counts = stats_helper.count_devis_by_status(devis_list)
        for code, label in DEVIS_STATUS_LABELS:
            self.devis_status_tiles[label].setText(str(counts[code]))

    def _refresh_top_organisateurs(self, prestations: list[Any], organizations: list[Any]) -> None:
        self._clear_layout(self.top_organisateurs_layout)
        ranking = stats_helper.top_organisateurs(prestations, organizations, limit=10)

        if not ranking:
            empty_label = QLabel("Aucun organisateur pour le moment.")
            style_muted_text(empty_label)
            self.top_organisateurs_layout.addWidget(empty_label)
            return

        for rank, (name, count) in enumerate(ranking, start=1):
            suffix = "prestation" if count == 1 else "prestations"
            line = QLabel(f"{rank}. {name} - {count} {suffix}")
            self.top_organisateurs_layout.addWidget(line)

    def _refresh_next_prestations(self, prestations: list[Any]) -> None:
        self._clear_layout(self.next_prestations_layout)
        upcoming = stats_helper.upcoming_prestations(prestations, limit=10)

        if not upcoming:
            empty_label = QLabel("Aucune prestation planifiee.")
            style_muted_text(empty_label)
            self.next_prestations_layout.addWidget(empty_label)
            return

        for prestation in upcoming:
            lieu = prestation.lieu_nom or prestation.lieu_city
            details = " - ".join(part for part in (prestation.date_debut, prestation.nom, lieu) if part)
            self.next_prestations_layout.addWidget(QLabel(details))

    @staticmethod
    def _clear_layout(layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
