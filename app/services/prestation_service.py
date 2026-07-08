from __future__ import annotations

from datetime import datetime

from app.models.prestation import Prestation
from app.repositories.prestation_repository import PrestationRepository


class PrestationService:
    STATUSES = {
        "prospection": "Prospection",
        "devis_envoye": "Devis envoye",
        "confirmee": "Confirmee",
        "realisee": "Realisee",
        "facturee": "Facturee",
        "soldee": "Soldee",
        "archivee": "Archivee",
        "annulee": "Annulee",
    }

    def __init__(self, repository: PrestationRepository | None = None) -> None:
        self.repository = repository or PrestationRepository()

    def list_prestations(self) -> list[Prestation]:
        return self.repository.get_all()

    def search_prestations(self, query: str) -> list[Prestation]:
        normalized_query = query.strip().casefold()

        if not normalized_query:
            return self.list_prestations()

        return [
            prestation
            for prestation in self.list_prestations()
            if normalized_query in self._search_text(prestation)
        ]

    def get_prestation(self, prestation_id: int) -> Prestation | None:
        return self.repository.get_by_id(prestation_id)

    def create_prestation(self, prestation: Prestation) -> int:
        self._prepare(prestation)
        prestation.reference = prestation.reference or self.next_reference()
        return self.repository.insert(prestation)

    def update_prestation(self, prestation: Prestation) -> None:
        if prestation.id is None:
            raise ValueError("Impossible de modifier une prestation sans identifiant.")

        self._prepare(prestation)
        self.repository.update(prestation)

    def delete_prestation(self, prestation_id: int) -> None:
        self.repository.delete(prestation_id)

    def next_reference(self) -> str:
        year = datetime.now().year
        sequence = self.repository.next_sequence(year)
        return f"PREST-{year}-{sequence:04d}"

    def _prepare(self, prestation: Prestation) -> None:
        prestation.type_evenement = str(prestation.type_evenement or "").strip()
        prestation.nom = str(prestation.nom or "").strip()
        prestation.date_debut = str(prestation.date_debut or "").strip()
        prestation.date_fin = str(prestation.date_fin or "").strip()
        prestation.lieu_nom = str(prestation.lieu_nom or "").strip()
        prestation.lieu_adresse = str(prestation.lieu_adresse or "").strip()
        prestation.lieu_postal_code = str(prestation.lieu_postal_code or "").strip()
        prestation.lieu_city = str(prestation.lieu_city or "").strip()
        prestation.notes = str(prestation.notes or "").strip()
        prestation.statut = prestation.statut or "prospection"

        if not prestation.nom:
            raise ValueError("Le nom de la prestation est obligatoire.")
        if not prestation.date_debut:
            raise ValueError("La date de la prestation est obligatoire.")

    def _search_text(self, prestation: Prestation) -> str:
        values = (
            prestation.reference,
            prestation.type_evenement,
            prestation.nom,
            prestation.lieu_nom,
            prestation.lieu_city,
            prestation.notes,
            self.STATUSES.get(prestation.statut, prestation.statut),
        )
        return " ".join(str(value or "") for value in values).casefold()
