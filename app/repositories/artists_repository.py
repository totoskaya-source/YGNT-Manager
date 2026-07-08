from __future__ import annotations

from typing import Any

from app.models.artist import Artist
from app.repositories.artist_repository import ArtistRepository


class ArtistsRepository:
    """Compatibility adapter for older code using dict/tuple artist data."""

    def __init__(self) -> None:
        self.repository = ArtistRepository()

    def get_all(self) -> list[tuple[Any, ...]]:
        return [
            (
                artist.id,
                artist.legal_name,
                "",
                artist.stage_name,
                artist.instrument,
                artist.status,
                artist.fee,
            )
            for artist in self.repository.get_all()
        ]

    def add(self, artiste: dict[str, Any]) -> int:
        legal_name = " ".join(
            value.strip()
            for value in (artiste["prenom"], artiste["nom"])
            if value.strip()
        )

        return self.repository.insert(
            Artist(
                legal_name=legal_name or artiste["nom"],
                stage_name=artiste["nom_scene"],
                instrument=artiste["instrument"],
                status=artiste["statut"],
                fee=self._to_float(artiste["cachet"]),
            )
        )

    def delete(self, artist_id: int) -> None:
        self.repository.delete(artist_id)

    def _to_float(self, value: Any) -> float:
        try:
            return float(str(value).replace(",", "."))
        except (TypeError, ValueError):
            return 0.0
