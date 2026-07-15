from __future__ import annotations

from app.models.artist import Artist
from .base_repository import BaseRepository


class ArtistRepository(BaseRepository):

    def get_all(self) -> list[Artist]:
        rows = self.fetch_all(
            """
            SELECT *
            FROM artists
            ORDER BY
                COALESCE(NULLIF(stage_name, ''), legal_name),
                legal_name
            """
        )
        return [Artist(**dict(r)) for r in rows]

    def get_by_id(self, artist_id: int) -> Artist | None:
        row = self.fetch_one(
            "SELECT * FROM artists WHERE id=?",
            (artist_id,)
        )
        return Artist(**dict(row)) if row else None

    def insert(self, artist: Artist) -> int:

        cursor = self.execute("""
            INSERT INTO artists(
                stage_name,
                legal_name,
                first_name,
                address,
                postal_code,
                city,
                email,
                phone,
                instrument,
                secondary_instruments,
                status,
                qualification,
                fee,
                birth_date,
                birth_place,
                social_number,
                conges_spectacle_number,
                siren,
                siret,
                ape,
                licence,
                iban,
                bic,
                notes,
                comments,
                style_musical,
                description,
                logo_path,
                photo_path,
                site_internet,
                facebook,
                instagram,
                youtube
            )
            VALUES(
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )
        """, (
            artist.stage_name,
            artist.legal_name,
            artist.first_name,
            artist.address,
            artist.postal_code,
            artist.city,
            artist.email,
            artist.phone,
            artist.instrument,
            artist.secondary_instruments,
            artist.status,
            artist.qualification,
            artist.fee,
            artist.birth_date,
            artist.birth_place,
            artist.social_number,
            artist.conges_spectacle_number,
            artist.siren,
            artist.siret,
            artist.ape,
            artist.licence,
            artist.iban,
            artist.bic,
            artist.notes,
            artist.comments,
            artist.style_musical,
            artist.description,
            artist.logo_path,
            artist.photo_path,
            artist.site_internet,
            artist.facebook,
            artist.instagram,
            artist.youtube,
        ))

        return cursor.lastrowid

    def update(self, artist: Artist) -> None:

        self.execute("""
            UPDATE artists SET

                stage_name=?,
                legal_name=?,
                first_name=?,
                address=?,
                postal_code=?,
                city=?,
                email=?,
                phone=?,
                instrument=?,
                secondary_instruments=?,
                status=?,
                qualification=?,
                fee=?,
                birth_date=?,
                birth_place=?,
                social_number=?,
                conges_spectacle_number=?,
                siren=?,
                siret=?,
                ape=?,
                licence=?,
                iban=?,
                bic=?,
                notes=?,
                comments=?,
                style_musical=?,
                description=?,
                logo_path=?,
                photo_path=?,
                site_internet=?,
                facebook=?,
                instagram=?,
                youtube=?,
                updated_at=CURRENT_TIMESTAMP

            WHERE id=?
        """, (

            artist.stage_name,
            artist.legal_name,
            artist.first_name,
            artist.address,
            artist.postal_code,
            artist.city,
            artist.email,
            artist.phone,
            artist.instrument,
            artist.secondary_instruments,
            artist.status,
            artist.qualification,
            artist.fee,
            artist.birth_date,
            artist.birth_place,
            artist.social_number,
            artist.conges_spectacle_number,
            artist.siren,
            artist.siret,
            artist.ape,
            artist.licence,
            artist.iban,
            artist.bic,
            artist.notes,
            artist.comments,
            artist.style_musical,
            artist.description,
            artist.logo_path,
            artist.photo_path,
            artist.site_internet,
            artist.facebook,
            artist.instagram,
            artist.youtube,
            artist.id

        ))

    def delete(self, artist_id: int) -> None:

        self.execute(
            "DELETE FROM artists WHERE id=?",
            (artist_id,)
        )
        
