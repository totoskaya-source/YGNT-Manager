from __future__ import annotations

from app.models.formation_artiste import FormationArtiste
from app.repositories.formation_artiste_repository import FormationArtisteRepository


class FormationArtisteService:
    """Gestion de la composition d'une Formation - onglet Composition
    (docs/PRESTATIONS_ARCHITECTURE.md, Sprint 18.0) : ajouter/supprimer un
    artiste, changer l'ordre, modifier le rôle. Donnee interne a la
    Formation ; jamais lue automatiquement par le contrat de cession, qui
    continue de n'utiliser que la Formation elle-meme (nom/style/logo/photo)."""

    def __init__(self, repository: FormationArtisteRepository | None = None) -> None:
        self.repository = repository or FormationArtisteRepository()

    def list_composition(self, formation_id: int) -> list[FormationArtiste]:
        return self.repository.list_for_formation(formation_id)

    def add_member(
        self,
        formation_id: int,
        artiste_id: int,
        role: str = "",
        ordre: int | None = None,
    ) -> int:
        if formation_id is None or artiste_id is None:
            raise ValueError("La formation et l'artiste sont obligatoires pour ajouter un membre.")

        if self.repository.find(formation_id, artiste_id) is not None:
            raise ValueError("Cet artiste fait déjà partie de la composition de cette formation.")

        if ordre is None:
            ordre = self.repository.max_ordre(formation_id) + 1

        member = FormationArtiste(
            formation_id=formation_id,
            artiste_id=artiste_id,
            role=str(role or "").strip(),
            ordre=ordre,
        )
        return self.repository.insert(member)

    def remove_member(self, member_id: int) -> None:
        self.repository.delete(member_id)

    def update_role(self, member_id: int, role: str) -> None:
        member = self.repository.get_by_id(member_id)
        if member is None:
            raise ValueError("Membre introuvable.")

        member.role = str(role or "").strip()
        self.repository.update(member)

    def move_up(self, member_id: int) -> None:
        self._swap_with_neighbor(member_id, direction=-1)

    def move_down(self, member_id: int) -> None:
        self._swap_with_neighbor(member_id, direction=1)

    def _swap_with_neighbor(self, member_id: int, direction: int) -> None:
        member = self.repository.get_by_id(member_id)
        if member is None or member.formation_id is None:
            return

        ordered = self.repository.list_for_formation(member.formation_id)
        position = next((i for i, m in enumerate(ordered) if m.id == member_id), None)
        if position is None:
            return

        neighbor_position = position + direction
        if neighbor_position < 0 or neighbor_position >= len(ordered):
            return

        neighbor = ordered[neighbor_position]
        member.ordre, neighbor.ordre = neighbor.ordre, member.ordre
        self.repository.update(member)
        self.repository.update(neighbor)
