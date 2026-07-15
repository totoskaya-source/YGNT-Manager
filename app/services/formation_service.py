from __future__ import annotations

from app.models.formation import Formation
from app.repositories.formation_repository import FormationRepository


class FormationService:
    def __init__(self, repository: FormationRepository | None = None) -> None:
        self.repository = repository or FormationRepository()

    def list_formations(self) -> list[Formation]:
        return self.repository.get_all()

    def search_formations(self, query: str) -> list[Formation]:
        normalized_query = query.strip().casefold()

        if not normalized_query:
            return self.list_formations()

        return [
            formation
            for formation in self.list_formations()
            if normalized_query in self._search_text(formation)
        ]

    def get_formation(self, formation_id: int) -> Formation | None:
        return self.repository.get_by_id(formation_id)

    def create_formation(self, formation: Formation) -> int:
        self._validate(formation)
        return self.repository.insert(formation)

    def update_formation(self, formation: Formation) -> None:
        if formation.id is None:
            raise ValueError("Impossible de modifier une formation sans identifiant.")

        self._validate(formation)
        self.repository.update(formation)

    def delete_formation(self, formation_id: int) -> None:
        self.repository.delete(formation_id)

    def _validate(self, formation: Formation) -> None:
        if not formation.nom.strip():
            raise ValueError("Le nom de la formation est obligatoire.")

        formation.nom = formation.nom.strip()
        formation.logo_path = formation.logo_path.strip()
        formation.photo_path = formation.photo_path.strip()
        formation.description = formation.description.strip()
        formation.style = formation.style.strip()

    def _search_text(self, formation: Formation) -> str:
        values = (formation.nom, formation.style, formation.description)
        return " ".join(str(value or "") for value in values).casefold()
