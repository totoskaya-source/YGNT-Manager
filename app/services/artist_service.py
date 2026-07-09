from __future__ import annotations

from app.models.artist import Artist
from app.repositories.artist_repository import ArtistRepository


class ArtistService:
    def __init__(self, repository: ArtistRepository | None = None) -> None:
        self.repository = repository or ArtistRepository()

    def list_artists(self) -> list[Artist]:
        return self.repository.get_all()

    def search_artists(self, query: str) -> list[Artist]:
        normalized_query = query.strip().casefold()

        if not normalized_query:
            return self.list_artists()

        return [
            artist
            for artist in self.list_artists()
            if normalized_query in self._search_text(artist)
        ]

    def get_artist(self, artist_id: int) -> Artist | None:
        return self.repository.get_by_id(artist_id)

    def create_artist(self, artist: Artist) -> int:
        self._validate(artist)
        return self.repository.insert(artist)

    def update_artist(self, artist: Artist) -> None:
        if artist.id is None:
            raise ValueError("Impossible de modifier un artiste sans identifiant.")

        self._validate(artist)
        self.repository.update(artist)

    def delete_artist(self, artist_id: int) -> None:
        self.repository.delete(artist_id)

    def _validate(self, artist: Artist) -> None:
        if not artist.legal_name.strip() and not artist.stage_name.strip():
            raise ValueError("Le nom legal ou le nom de scene est obligatoire.")

        artist.legal_name = artist.legal_name.strip()
        artist.stage_name = artist.stage_name.strip()
        artist.email = artist.email.strip()
        artist.phone = artist.phone.strip()
        artist.instrument = artist.instrument.strip()
        artist.status = artist.status.strip()
        artist.city = artist.city.strip()
        artist.notes = artist.notes.strip()

        # Champs marketing/informatifs uniquement : jamais utilises dans un
        # devis, un contrat ou une facture.
        artist.style_musical = artist.style_musical.strip()
        artist.description = artist.description.strip()
        artist.logo_path = artist.logo_path.strip()
        artist.photo_path = artist.photo_path.strip()
        artist.site_internet = artist.site_internet.strip()
        artist.facebook = artist.facebook.strip()
        artist.instagram = artist.instagram.strip()
        artist.youtube = artist.youtube.strip()

        # Le cachet habituel (fee) n'est plus lu ni ecrit par le service : la
        # colonne reste en base pour compatibilite mais n'est plus utilisee
        # (Sprint 8.7). ArtistDialog transmet toujours la valeur deja stockee,
        # jamais une saisie utilisateur.

    def _search_text(self, artist: Artist) -> str:
        values = (
            artist.legal_name,
            artist.stage_name,
            artist.instrument,
            artist.status,
            artist.email,
            artist.phone,
            artist.city,
            artist.notes,
        )
        return " ".join(str(value or "") for value in values).casefold()
