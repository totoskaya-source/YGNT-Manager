from __future__ import annotations

from app.models.prestation import Prestation
from .base_repository import BaseRepository


class PrestationRepository(BaseRepository):

    def get_all(self) -> list[Prestation]:
        rows = self.fetch_all(
            """
            SELECT *
            FROM prestations
            ORDER BY date_debut DESC, id DESC
            """
        )
        return [Prestation(**dict(r)) for r in rows]

    def get_by_id(self, prestation_id: int) -> Prestation | None:
        row = self.fetch_one(
            "SELECT * FROM prestations WHERE id=?",
            (prestation_id,)
        )
        return Prestation(**dict(row)) if row else None

    def insert(self, prestation: Prestation) -> int:

        cursor = self.execute("""
            INSERT INTO prestations(
                reference,
                type_evenement,
                nom,
                statut,
                date_debut,
                date_fin,
                artist_id,
                organization_id,
                lieu_nom,
                lieu_adresse,
                lieu_postal_code,
                lieu_city,
                notes
            )
            VALUES(
                ?,?,?,?,?,?,?,?,?,?,?,?,?
            )
        """, (
            prestation.reference,
            prestation.type_evenement,
            prestation.nom,
            prestation.statut,
            prestation.date_debut,
            prestation.date_fin,
            prestation.artist_id,
            prestation.organization_id,
            prestation.lieu_nom,
            prestation.lieu_adresse,
            prestation.lieu_postal_code,
            prestation.lieu_city,
            prestation.notes,
        ))

        return cursor.lastrowid

    def update(self, prestation: Prestation) -> None:

        self.execute("""
            UPDATE prestations SET

                reference=?,
                type_evenement=?,
                nom=?,
                statut=?,
                date_debut=?,
                date_fin=?,
                artist_id=?,
                organization_id=?,
                lieu_nom=?,
                lieu_adresse=?,
                lieu_postal_code=?,
                lieu_city=?,
                notes=?,
                updated_at=CURRENT_TIMESTAMP

            WHERE id=?
        """, (

            prestation.reference,
            prestation.type_evenement,
            prestation.nom,
            prestation.statut,
            prestation.date_debut,
            prestation.date_fin,
            prestation.artist_id,
            prestation.organization_id,
            prestation.lieu_nom,
            prestation.lieu_adresse,
            prestation.lieu_postal_code,
            prestation.lieu_city,
            prestation.notes,
            prestation.id

        ))

    def delete(self, prestation_id: int) -> None:

        self.execute(
            "DELETE FROM prestations WHERE id=?",
            (prestation_id,)
        )

    def next_sequence(self, year: int) -> int:
        row = self.fetch_one(
            """
            SELECT reference
            FROM prestations
            WHERE reference LIKE ?
            ORDER BY reference DESC
            LIMIT 1
            """,
            (f"PREST-{year}-%",),
        )

        if row is None or not row["reference"]:
            return 1

        try:
            return int(str(row["reference"]).split("-")[-1]) + 1
        except ValueError:
            return 1
