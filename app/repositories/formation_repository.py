from __future__ import annotations

from app.models.formation import Formation
from app.repositories.base_repository import BaseRepository


class FormationRepository(BaseRepository):

    def get_all(self) -> list[Formation]:
        rows = self.fetch_all(
            """
            SELECT *
            FROM formations
            ORDER BY nom
            """
        )
        return [Formation(**dict(row)) for row in rows]

    def get_by_id(self, formation_id: int) -> Formation | None:
        row = self.fetch_one(
            "SELECT * FROM formations WHERE id=?",
            (formation_id,),
        )
        return Formation(**dict(row)) if row else None

    def insert(self, formation: Formation) -> int:
        cursor = self.execute(
            """
            INSERT INTO formations(
                nom, logo_path, photo_path, description, style,
                address, postal_code, city, phone, email,
                siret, ape, licence, iban, bic
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                formation.nom,
                formation.logo_path,
                formation.photo_path,
                formation.description,
                formation.style,
                formation.address,
                formation.postal_code,
                formation.city,
                formation.phone,
                formation.email,
                formation.siret,
                formation.ape,
                formation.licence,
                formation.iban,
                formation.bic,
            ),
        )
        return int(cursor.lastrowid)

    def update(self, formation: Formation) -> None:
        self.execute(
            """
            UPDATE formations
            SET nom=?,
                logo_path=?,
                photo_path=?,
                description=?,
                style=?,
                address=?,
                postal_code=?,
                city=?,
                phone=?,
                email=?,
                siret=?,
                ape=?,
                licence=?,
                iban=?,
                bic=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (
                formation.nom,
                formation.logo_path,
                formation.photo_path,
                formation.description,
                formation.style,
                formation.address,
                formation.postal_code,
                formation.city,
                formation.phone,
                formation.email,
                formation.siret,
                formation.ape,
                formation.licence,
                formation.iban,
                formation.bic,
                formation.id,
            ),
        )

    def delete(self, formation_id: int) -> None:
        self.execute("DELETE FROM formations WHERE id=?", (formation_id,))
