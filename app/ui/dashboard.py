from __future__ import annotations

from typing import Any, Callable

from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.services import stats_helper
from app.services.contract_service import ContractService
from app.services.contrat_cddu_service import ContratCdduService
from app.services.devis_service import DevisService
from app.services.facture_service import FactureService
from app.services.paiement_service import PaiementService
from app.services.prestation_service import PrestationService
from app.services.producteur_service import ProducteurService
from app.ui.contract_dialog import ContractDialog
from app.ui.devis_dialog import DevisDialog
from app.ui.facture_dialog import FactureDialog
from app.ui.paiement_dialog import PaiementDialog
from app.ui.prestation_dialog import PrestationDialog
from app.ui.theme import (
    style_dashboard_greeting,
    style_muted_text,
    style_page_title,
    style_stat_label,
    style_stat_value,
)

INDICATOR_LABELS = ("Prestations", "Devis", "Contrats", "Factures", "Paiements")
BILLING_LABELS = ("CA facture", "CA encaisse", "Factures impayees", "Paiements en attente")
ALERT_LABELS = ("Factures en retard", "Devis a relancer", "Prestations sans facture", "CDDU a preparer")


class DashboardPage(QWidget):
    """Page d'accueil de YGNT Manager : vue d'ensemble de l'activité.

    Consultation et navigation uniquement : aucune logique metier n'est
    recalculee ici, chaque chiffre provient d'une liste déjà exposee par un
    Service existant (une seule requete par module, jamais repetee entre les
    sections du Dashboard)."""

    def __init__(
        self,
        prestation_service: PrestationService | None = None,
        devis_service: DevisService | None = None,
        contract_service: ContractService | None = None,
        facture_service: FactureService | None = None,
        paiement_service: PaiementService | None = None,
        producteur_service: ProducteurService | None = None,
        contrat_cddu_service: ContratCdduService | None = None,
    ) -> None:
        super().__init__()

        self.prestation_service = prestation_service or PrestationService()
        self.devis_service = devis_service or DevisService()
        self.contract_service = contract_service or ContractService()
        self.facture_service = facture_service or FactureService()
        self.paiement_service = paiement_service or PaiementService(facture_service=self.facture_service)
        self.producteur_service = producteur_service or ProducteurService()
        self.contrat_cddu_service = contrat_cddu_service or ContratCdduService()

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

        title = QLabel("Tableau de bord")
        style_page_title(title)
        layout.addWidget(title)

        self.greeting_label = QLabel()
        style_dashboard_greeting(self.greeting_label)
        layout.addWidget(self.greeting_label)

        alerts_card, self.alert_tiles = self._build_stats_card("⚠ A traiter", ALERT_LABELS)
        layout.addWidget(alerts_card)

        next_prestation_card, self.next_prestation_label = self._build_text_card("Prochaine prestation")
        layout.addWidget(next_prestation_card)

        indicators_card, self.indicator_tiles = self._build_stats_card("Indicateurs", INDICATOR_LABELS)
        layout.addWidget(indicators_card)

        billing_card, self.billing_tiles = self._build_stats_card("Facturation", BILLING_LABELS)
        layout.addWidget(billing_card)

        layout.addWidget(self._build_quick_actions_card())

        activity_card, self.activity_layout = self._build_card("Dernières activités")
        layout.addWidget(activity_card)

        layout.addStretch()

        self.refresh()

    # ===== Construction des cartes =====

    @staticmethod
    def _build_card(title: str) -> tuple[QGroupBox, QVBoxLayout]:
        card = QGroupBox(title)
        layout = QVBoxLayout(card)
        layout.setSpacing(8)
        return card, layout

    def _build_text_card(self, title: str) -> tuple[QGroupBox, QLabel]:
        card, layout = self._build_card(title)
        label = QLabel()
        label.setWordWrap(True)
        layout.addWidget(label)
        return card, label

    def _build_stats_card(self, title: str, labels: tuple[str, ...]) -> tuple[QGroupBox, dict[str, QLabel]]:
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

    def _build_quick_actions_card(self) -> QGroupBox:
        card, layout = self._build_card("Actions rapides")

        actions = QHBoxLayout()
        actions.setSpacing(8)

        buttons: tuple[tuple[str, Callable[[], None]], ...] = (
            ("Nouvelle prestation", self.new_prestation),
            ("Nouveau devis", self.new_devis),
            ("Nouveau contrat", self.new_contract),
            ("Nouvelle facture", self.new_facture),
            ("Nouveau paiement", self.new_paiement),
        )

        for label_text, handler in buttons:
            button = QPushButton(label_text)
            button.clicked.connect(handler)
            actions.addWidget(button)

        actions.addStretch()
        layout.addLayout(actions)
        return card

    # ===== Actions rapides =====

    def new_prestation(self) -> None:
        dialog = PrestationDialog(self, service=self.prestation_service)

        if dialog.exec():
            try:
                self.prestation_service.create_prestation(dialog.prestation)
            except ValueError as exc:
                QMessageBox.warning(self, "Prestation invalide", str(exc))
                return

        self.refresh()

    def new_devis(self) -> None:
        # Le dialogue s'enregistre lui-meme et reste ouvert (Sprint 12.0) :
        # on rafraichit simplement le Dashboard a la fermeture.
        dialog = DevisDialog(self, service=self.devis_service)
        dialog.exec()
        self.refresh()

    def new_contract(self) -> None:
        dialog = ContractDialog(self, service=self.contract_service)
        dialog.exec()
        self.refresh()

    def new_facture(self) -> None:
        dialog = FactureDialog(self, service=self.facture_service)
        dialog.exec()
        self.refresh()

    def new_paiement(self) -> None:
        dialog = PaiementDialog(self, service=self.paiement_service, facture_service=self.facture_service)

        if dialog.exec():
            try:
                self.paiement_service.create_paiement(dialog.paiement)
            except ValueError as exc:
                QMessageBox.warning(self, "Paiement invalide", str(exc))
                return

        self.refresh()

    # ===== Rafraichissement =====

    def refresh(self) -> None:
        # Une seule requete par module : toutes les sections ci-dessous
        # reutilisent ces memes listes, jamais de requete redondante.
        prestations = self.prestation_service.list_prestations()
        devis_list = self.devis_service.list_devis()
        contracts = self.contract_service.list_contracts()
        factures = self.facture_service.list_factures()
        paiements = self.paiement_service.list_paiements()
        contrats_cddu = self.contrat_cddu_service.list_contrats()

        self._refresh_greeting()
        self._refresh_alerts(prestations, devis_list, factures, contrats_cddu)
        self._refresh_next_prestation(prestations)
        self._refresh_indicators(prestations, devis_list, contracts, factures, paiements)
        self._refresh_billing(factures, paiements)
        self._refresh_activity(prestations, devis_list, contracts, factures, paiements)

    def _refresh_greeting(self) -> None:
        producteur = self.producteur_service.get_active_producteur()

        if producteur is None:
            self.greeting_label.setText("Bienvenue sur YGNT Manager")
            return

        representant = str(producteur.representant or "").strip()
        if representant:
            self.greeting_label.setText(f"Bonjour {representant.split()[0]}")
            return

        nom = str(producteur.nom or "").strip()
        if nom:
            self.greeting_label.setText(f"Bonjour {nom}")
            return

        self.greeting_label.setText("Bienvenue sur YGNT Manager")

    def _refresh_alerts(
        self,
        prestations: list[Any],
        devis_list: list[Any],
        factures: list[Any],
        contrats_cddu: list[Any],
    ) -> None:
        # Chaque compteur reutilise une fonction pure de stats_helper : aucun
        # calcul metier ici, uniquement la mise en forme du chiffre.
        self.alert_tiles["Factures en retard"].setText(str(len(stats_helper.factures_en_retard(factures))))
        self.alert_tiles["Devis a relancer"].setText(str(len(stats_helper.devis_expirant_bientot(devis_list))))
        self.alert_tiles["Prestations sans facture"].setText(
            str(len(stats_helper.prestations_sans_facture(prestations, factures)))
        )
        self.alert_tiles["CDDU a preparer"].setText(
            str(len(stats_helper.cddu_a_preparer(prestations, contrats_cddu)))
        )

    def _refresh_next_prestation(self, prestations: list[Any]) -> None:
        upcoming = stats_helper.upcoming_prestations(prestations, limit=1)

        if not upcoming:
            self.next_prestation_label.setText("Aucune prestation planifiée.")
            return

        prestation = upcoming[0]
        lieu = prestation.lieu_nom or prestation.lieu_city
        details = " - ".join(part for part in (prestation.date_debut, prestation.nom, lieu) if part)
        self.next_prestation_label.setText(details)

    def _refresh_indicators(
        self,
        prestations: list[Any],
        devis_list: list[Any],
        contracts: list[Any],
        factures: list[Any],
        paiements: list[Any],
    ) -> None:
        self.indicator_tiles["Prestations"].setText(str(len(prestations)))
        self.indicator_tiles["Devis"].setText(str(len(devis_list)))
        self.indicator_tiles["Contrats"].setText(str(len(contracts)))
        self.indicator_tiles["Factures"].setText(str(len(factures)))
        self.indicator_tiles["Paiements"].setText(str(len(paiements)))

    def _refresh_billing(self, factures: list[Any], paiements: list[Any]) -> None:
        # Calculs partages avec la page Statistiques (cf. app/services/stats_helper.py) :
        # jamais recalcules deux fois.
        self.billing_tiles["CA facture"].setText(f"{stats_helper.ca_facture(factures):.2f} EUR")
        self.billing_tiles["CA encaisse"].setText(f"{stats_helper.ca_encaisse(paiements):.2f} EUR")
        self.billing_tiles["Factures impayees"].setText(str(stats_helper.factures_impayees_count(factures)))
        self.billing_tiles["Paiements en attente"].setText(str(stats_helper.paiements_en_attente_count(paiements)))

    def _refresh_activity(
        self,
        prestations: list[Any],
        devis_list: list[Any],
        contracts: list[Any],
        factures: list[Any],
        paiements: list[Any],
    ) -> None:
        entries: list[tuple[str, str, str]] = []

        for prestation in prestations:
            entries.append((prestation.created_at or "", "Prestation", prestation.nom or prestation.reference))
        for devis in devis_list:
            entries.append((devis.created_at or "", "Devis", devis.devis_number or devis.spectacle_nom))
        for contract in contracts:
            entries.append((contract.created_at or "", "Contrat", contract.contract_number or contract.spectacle_nom))
        for facture in factures:
            entries.append((facture.created_at or "", "Facture", facture.facture_number or facture.spectacle_nom))
        for paiement in paiements:
            entries.append((paiement.created_at or "", "Paiement", paiement.reference))

        # Le format CURRENT_TIMESTAMP (AAAA-MM-JJ HH:MM:SS) se trie
        # correctement en tant que texte : pas besoin de parser les dates.
        entries = sorted((entry for entry in entries if entry[0]), key=lambda entry: entry[0], reverse=True)

        self._clear_layout(self.activity_layout)

        if not entries:
            empty_label = QLabel("Aucune activité pour le moment.")
            style_muted_text(empty_label)
            self.activity_layout.addWidget(empty_label)
            return

        for _created_at, kind, description in entries[:5]:
            line = QLabel(f"{kind} - {description or '-'}")
            self.activity_layout.addWidget(line)

    @staticmethod
    def _clear_layout(layout: QLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
