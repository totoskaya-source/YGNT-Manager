from __future__ import annotations

from datetime import datetime

from app.models.facture import Facture
from app.models.paiement import Paiement
from app.repositories.paiement_repository import PaiementRepository
from app.services.facture_service import FactureService


class PaiementService:
    STATUSES = {
        "pending": "En attente",
        "partial": "Partiel",
        "paid": "Paye",
        "cancelled": "Annule",
    }

    def __init__(
        self,
        repository: PaiementRepository | None = None,
        facture_service: FactureService | None = None,
    ) -> None:
        self.repository = repository or PaiementRepository()
        self.facture_service = facture_service or FactureService()

    def list_paiements(self) -> list[Paiement]:
        return self.repository.get_all()

    def search_paiements(self, query: str = "", status: str = "all") -> list[Paiement]:
        normalized_query = query.strip().casefold()
        items = self.list_paiements()

        if status != "all":
            items = [paiement for paiement in items if paiement.status == status]

        if not normalized_query:
            return items

        factures_by_id = {facture.id: facture for facture in self.facture_service.list_factures()}
        return [
            paiement
            for paiement in items
            if normalized_query in self._search_text(paiement, factures_by_id.get(paiement.facture_id))
        ]

    def list_for_facture(self, facture_id: int) -> list[Paiement]:
        """Paiements rattaches a une facture, via facture_id : relation
        obligatoire (un paiement appartient TOUJOURS a une facture), a la
        difference de prestation_id sur Devis/Facture qui reste optionnel."""
        return self.repository.get_for_facture(facture_id)

    def list_for_prestation(self, prestation_id: int) -> list[Paiement]:
        """Paiements rattaches (indirectement, via leur Facture) a une
        Prestation. Un Paiement n'a pas de prestation_id propre : cette
        methode reutilise FactureService.list_for_prestation() puis
        list_for_facture() pour chaque facture, sans dupliquer la logique de
        filtrage."""
        factures = self.facture_service.list_for_prestation(prestation_id)
        paiements: list[Paiement] = []
        for facture in factures:
            if facture.id is not None:
                paiements.extend(self.list_for_facture(facture.id))
        return paiements

    def get_paiement(self, paiement_id: int) -> Paiement | None:
        return self.repository.get_by_id(paiement_id)

    def build_from_facture(self, facture: Facture) -> Paiement:
        """Prepare un paiement pre-rempli (facture, montant restant, mode de
        paiement ; l'echeance de la facture est reportee en observations
        faute de champ dedie sur Paiement) a partir d'une Facture. Le
        paiement n'est pas enregistre : nouveau document independant,
        toujours modifiable avant validation. La Facture n'est JAMAIS
        modifiee (meme philosophie que FactureService.build_from_contract)."""
        montant_restant = self.solde_restant(facture.id) if facture.id is not None else float(facture.montant or 0)

        return Paiement(
            facture_id=facture.id,
            montant=max(montant_restant, 0.0),
            mode_paiement=facture.mode_paiement,
            observations=f"Echeance facture : {facture.echeance}" if facture.echeance else "",
        )

    def create_paiement(self, paiement: Paiement) -> int:
        self._prepare(paiement)
        paiement.reference = paiement.reference or self.next_paiement_number()
        paiement_id = self.repository.insert(paiement)
        self._sync_facture_status(paiement.facture_id)
        return paiement_id

    def update_paiement(self, paiement: Paiement) -> None:
        if paiement.id is None:
            raise ValueError("Impossible de modifier un paiement sans identifiant.")

        previous = self.get_paiement(paiement.id)
        self._prepare(paiement)
        self.repository.update(paiement)

        self._sync_facture_status(paiement.facture_id)
        if previous is not None and previous.facture_id != paiement.facture_id:
            self._sync_facture_status(previous.facture_id)

    def delete_paiement(self, paiement_id: int) -> None:
        paiement = self.get_paiement(paiement_id)
        self.repository.delete(paiement_id)
        if paiement is not None:
            self._sync_facture_status(paiement.facture_id)

    def next_paiement_number(self) -> str:
        year = datetime.now().year
        sequence = self.repository.next_sequence(year)
        return f"PAI-{year}-{sequence:04d}"

    def total_paid(self, facture_id: int) -> float:
        """Somme des paiements valides (statut different de 'cancelled')
        deja enregistres pour cette facture."""
        paiements = self.list_for_facture(facture_id)
        return round(
            sum(float(p.montant or 0) for p in paiements if p.status != "cancelled"),
            2,
        )

    def _credite(self, facture_id: int) -> float:
        """Total deja couvert sur cette facture : l'acompte indique sur la
        facture (jamais un paiement enregistre automatiquement) plus les
        paiements effectivement enregistres. Base commune a solde_restant()
        et compute_facture_status() pour que les deux restent toujours
        coherents entre eux (Sprint 12.7)."""
        facture = self._require_facture(facture_id)
        return float(facture.acompte or 0) + self.total_paid(facture_id)

    def solde_restant(self, facture_id: int) -> float:
        """Montant reellement restant du sur cette facture : montant TTC
        diminue de l'acompte deja precise sur la facture ET des paiements
        enregistres. Ne descend jamais sous zero (un trop-percu eventuel
        n'apparait pas ici en negatif). Lecture seule : ne modifie jamais la
        facture."""
        facture = self._require_facture(facture_id)
        montant = float(facture.montant or 0)
        return round(max(montant - self._credite(facture_id), 0.0), 2)

    def compute_facture_status(self, facture_id: int) -> str:
        """Determine automatiquement l'etat de reglement d'une facture a
        partir de l'acompte et des paiements : rien de couvert -> 'pending'
        (En attente), couverture partielle -> 'partial' (Partiel), montant
        TTC entierement couvert (acompte + paiements) -> 'paid' (Paye).
        Calcul pur, en lecture seule : ne modifie JAMAIS la facture
        elle-meme. Utilise par _sync_facture_status() pour appliquer
        automatiquement le resultat (jamais duplique)."""
        facture = self._require_facture(facture_id)
        montant = float(facture.montant or 0)
        credite = self._credite(facture_id)

        if credite <= 0:
            return "pending"
        if credite < montant:
            return "partial"
        return "paid"

    def preview(self, paiement: Paiement) -> str:
        self._prepare(paiement)
        facture = self.facture_service.get_facture(paiement.facture_id)

        lines = [
            f"Reference : {paiement.reference or '(automatique)'}",
            f"Date : {paiement.date_paiement or '-'}",
            f"Statut : {self.STATUSES.get(paiement.status, paiement.status)}",
            f"Facture : {facture.facture_number if facture else '-'}",
            f"Organisateur : {facture.organisateur_structure if facture else '-'}",
            f"Montant du paiement : {float(paiement.montant or 0):.2f} EUR",
            f"Mode de paiement : {paiement.mode_paiement or '-'}",
            f"Reference bancaire : {paiement.reference_bancaire or '-'}",
        ]

        if facture is not None and facture.id is not None:
            lines.extend([
                f"Montant facture : {float(facture.montant or 0):.2f} EUR",
                f"Deja paye : {self.total_paid(facture.id):.2f} EUR",
                f"Reste a payer : {self.solde_restant(facture.id):.2f} EUR",
            ])

        if paiement.observations:
            lines.extend(["", "Observations", str(paiement.observations)])

        return "\n".join(lines)

    def _search_text(self, paiement: Paiement, facture: Facture | None) -> str:
        values = (
            paiement.reference,
            paiement.date_paiement,
            paiement.mode_paiement,
            paiement.reference_bancaire,
            paiement.observations,
            paiement.status_label,
            facture.facture_number if facture else "",
            facture.organisateur_structure if facture else "",
        )
        return " ".join(str(value or "") for value in values).casefold()

    def _prepare(self, paiement: Paiement) -> None:
        paiement.reference = str(paiement.reference or "").strip()
        paiement.date_paiement = str(paiement.date_paiement or "").strip()
        paiement.mode_paiement = str(paiement.mode_paiement or "").strip()
        paiement.reference_bancaire = str(paiement.reference_bancaire or "").strip()
        paiement.observations = str(paiement.observations or "").strip()
        paiement.status = paiement.status or "pending"

        if paiement.facture_id is None:
            raise ValueError("Le paiement doit etre rattache a une facture.")

        self._require_facture(paiement.facture_id)

        if not paiement.date_paiement:
            raise ValueError("La date du paiement est obligatoire.")

        try:
            paiement.montant = float(paiement.montant or 0)
        except (TypeError, ValueError):
            paiement.montant = 0.0

        if paiement.montant <= 0:
            raise ValueError("Le montant du paiement doit etre superieur a zero.")

    def _require_facture(self, facture_id: int) -> Facture:
        facture = self.facture_service.get_facture(facture_id)
        if facture is None:
            raise ValueError("La facture rattachee est introuvable.")
        return facture

    def _sync_facture_status(self, facture_id: int | None) -> None:
        """Met a jour automatiquement UNIQUEMENT le statut de la facture
        liee, a partir de compute_facture_status() (jamais duplique). Aucun
        autre champ de la facture (montant inclus) n'est touche."""
        if facture_id is None:
            return
        status = self.compute_facture_status(facture_id)
        self.facture_service.update_status(facture_id, status)
