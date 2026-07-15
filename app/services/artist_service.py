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
        # Toutes les valeurs passent par (value or "") avant .strip() : un
        # champ optionnel jamais renseigne est NULL en SQLite, donc None une
        # fois reconstruit par ArtistRepository (Artist(**dict(row))) - un
        # .strip() direct sur None levait AttributeError et interrompait
        # l'enregistrement AVANT d'atteindre l'UPDATE (cause reelle du bug
        # "champs non sauvegardes" : ce n'etait pas un probleme de
        # sauvegarde, l'appel plantait avant).
        if not (artist.legal_name or "").strip() and not (artist.stage_name or "").strip():
            raise ValueError("Le nom légal ou le nom de scène est obligatoire.")

        artist.qualification = (artist.qualification or "").strip()
        if not artist.qualification:
            # Obligatoire (Sprint 18.2) : le CDDU affiche "en qualite de
            # {{qualification}}" sans jamais coder de valeur par defaut en
            # dur - la donnee doit toujours venir de cette fiche. En
            # pratique, le QComboBox d'ArtistDialog ne transmet jamais de
            # chaine vide (il a toujours une selection courante) : cette
            # exception ne protege que les appels directs au Service.
            raise ValueError("La qualification est obligatoire.")

        artist.legal_name = (artist.legal_name or "").strip()
        artist.first_name = (artist.first_name or "").strip()
        artist.stage_name = (artist.stage_name or "").strip()
        artist.address = (artist.address or "").strip()
        artist.postal_code = (artist.postal_code or "").strip()
        artist.city = (artist.city or "").strip()
        artist.email = (artist.email or "").strip()
        artist.phone = (artist.phone or "").strip()
        artist.instrument = (artist.instrument or "").strip()
        artist.secondary_instruments = (artist.secondary_instruments or "").strip()
        artist.status = (artist.status or "").strip()
        artist.birth_date = (artist.birth_date or "").strip()
        artist.birth_place = (artist.birth_place or "").strip()
        artist.social_number = (artist.social_number or "").strip()
        artist.conges_spectacle_number = (artist.conges_spectacle_number or "").strip()
        artist.siren = (artist.siren or "").strip()
        artist.siret = (artist.siret or "").strip()
        artist.ape = (artist.ape or "").strip()
        artist.licence = (artist.licence or "").strip()
        artist.iban = (artist.iban or "").strip()
        artist.bic = (artist.bic or "").strip()
        artist.notes = (artist.notes or "").strip()
        artist.comments = (artist.comments or "").strip()

        # Champs marketing/informatifs uniquement : jamais utilises dans un
        # devis, un contrat ou une facture.
        artist.style_musical = (artist.style_musical or "").strip()
        artist.description = (artist.description or "").strip()
        artist.logo_path = (artist.logo_path or "").strip()
        artist.photo_path = (artist.photo_path or "").strip()
        artist.site_internet = (artist.site_internet or "").strip()
        artist.facebook = (artist.facebook or "").strip()
        artist.instagram = (artist.instagram or "").strip()
        artist.youtube = (artist.youtube or "").strip()

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
