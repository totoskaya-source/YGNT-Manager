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
                address,
                postal_code,
                city,
                email,
                phone,
                instrument,
                status,
                fee,
                birth_date,
                social_number,
                siren,
                siret,
                ape,
                licence,
                iban,
                bic,
                notes
            )
            VALUES(
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )
        """, (
            artist.stage_name,
            artist.legal_name,
            artist.address,
            artist.postal_code,
            artist.city,
            artist.email,
            artist.phone,
            artist.instrument,
            artist.status,
            artist.fee,
            artist.birth_date,
            artist.social_number,
            artist.siren,
            artist.siret,
            artist.ape,
            artist.licence,
            artist.iban,
            artist.bic,
            artist.notes
        ))

        return cursor.lastrowid

    def update(self, artist: Artist) -> None:

        self.execute("""
            UPDATE artists SET

                stage_name=?,
                legal_name=?,
                address=?,
                postal_code=?,
                city=?,
                email=?,
                phone=?,
                instrument=?,
                status=?,
                fee=?,
                birth_date=?,
                social_number=?,
                siren=?,
                siret=?,
                ape=?,
                licence=?,
                iban=?,
                bic=?,
                notes=?,
                updated_at=CURRENT_TIMESTAMP

            WHERE id=?
        """, (

            artist.stage_name,
            artist.legal_name,
            artist.address,
            artist.postal_code,
            artist.city,
            artist.email,
            artist.phone,
            artist.instrument,
            artist.status,
            artist.fee,
            artist.birth_date,
            artist.social_number,
            artist.siren,
            artist.siret,
            artist.ape,
            artist.licence,
            artist.iban,
            artist.bic,
            artist.notes,
            artist.id

        ))

    def delete(self, artist_id: int) -> None:

        self.execute(
            "DELETE FROM artists WHERE id=?",
            (artist_id,)
        )
        
