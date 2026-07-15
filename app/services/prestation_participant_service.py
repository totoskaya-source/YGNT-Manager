from __future__ import annotations

from app.models.prestation_participant import PrestationParticipant
from app.repositories.prestation_participant_repository import PrestationParticipantRepository


class PrestationParticipantService:
    """Équipe de prestation - couche metier de la relation many-to-many
    Prestation <-> Artiste (voir docs/PRESTATIONS_ARCHITECTURE.md).

    Donnee strictement interne. Ce service ne doit jamais être appele par
    ContractService/DevisService/FactureService : le contrat de cession, le
    devis et la facture continuent de fonctionner uniquement avec
    Organisateur / Formation / Prestation, sans aucun artiste injecte
    automatiquement (regle intangible du Sprint 15.5)."""

    def __init__(self, repository: PrestationParticipantRepository | None = None) -> None:
        self.repository = repository or PrestationParticipantRepository()

    def list_participants(self, prestation_id: int) -> list[PrestationParticipant]:
        return self.repository.list_for_prestation(prestation_id)

    def list_prestations_for_artiste(self, artiste_id: int) -> list[PrestationParticipant]:
        return self.repository.list_for_artiste(artiste_id)

    def get_participant(self, participant_id: int) -> PrestationParticipant | None:
        return self.repository.get_by_id(participant_id)

    def add_participant(
        self,
        prestation_id: int,
        artiste_id: int,
        role: str = "",
        ordre: int | None = None,
    ) -> int:
        if prestation_id is None or artiste_id is None:
            raise ValueError("La prestation et l'artiste sont obligatoires pour ajouter un participant.")

        if self.repository.find(prestation_id, artiste_id) is not None:
            raise ValueError("Cet artiste fait déjà partie de l'équipe de cette prestation.")

        participant = PrestationParticipant(
            prestation_id=prestation_id,
            artiste_id=artiste_id,
            role=str(role or "").strip(),
            ordre=ordre,
        )
        return self.repository.insert(participant)

    def update_participant(self, participant: PrestationParticipant) -> None:
        if participant.id is None:
            raise ValueError("Impossible de modifier un participant sans identifiant.")

        participant.role = str(participant.role or "").strip()
        self.repository.update(participant)

    def remove_participant(self, participant_id: int) -> None:
        self.repository.delete(participant_id)

    def remove_artiste_from_prestation(self, prestation_id: int, artiste_id: int) -> None:
        self.repository.delete_for_prestation_and_artiste(prestation_id, artiste_id)
