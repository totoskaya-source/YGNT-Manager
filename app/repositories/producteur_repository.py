from __future__ import annotations

from app.models.producteur import Producteur
from .base_repository import BaseRepository


class ProducteurRepository(BaseRepository):

    def get_all(self) -> list[Producteur]:
        rows = self.fetch_all(
            """
            SELECT *
            FROM producteurs
            ORDER BY nom
            """
        )
        return [self._from_row(r) for r in rows]

    def get_by_id(self, producteur_id: int) -> Producteur | None:
        row = self.fetch_one(
            "SELECT * FROM producteurs WHERE id=?",
            (producteur_id,)
        )
        return self._from_row(row) if row else None

    def get_active(self) -> Producteur | None:
        row = self.fetch_one(
            "SELECT * FROM producteurs WHERE actif=1 LIMIT 1"
        )
        return self._from_row(row) if row else None

    def insert(self, producteur: Producteur) -> int:

        cursor = self.execute("""
            INSERT INTO producteurs(
                nom,
                forme_juridique,
                adresse,
                postal_code,
                city,
                siret,
                ape,
                licence,
                tva,
                iban,
                bic,
                representant,
                fonction,
                convention_collective,
                logo_path,
                site_internet,
                email,
                phone,
                notes,
                actif
            )
            VALUES(
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )
        """, (
            producteur.nom,
            producteur.forme_juridique,
            producteur.adresse,
            producteur.postal_code,
            producteur.city,
            producteur.siret,
            producteur.ape,
            producteur.licence,
            producteur.tva,
            producteur.iban,
            producteur.bic,
            producteur.representant,
            producteur.fonction,
            producteur.convention_collective,
            producteur.logo_path,
            producteur.site_internet,
            producteur.email,
            producteur.phone,
            producteur.notes,
            int(producteur.actif),
        ))

        return cursor.lastrowid

    def update(self, producteur: Producteur) -> None:

        self.execute("""
            UPDATE producteurs SET

                nom=?,
                forme_juridique=?,
                adresse=?,
                postal_code=?,
                city=?,
                siret=?,
                ape=?,
                licence=?,
                tva=?,
                iban=?,
                bic=?,
                representant=?,
                fonction=?,
                convention_collective=?,
                logo_path=?,
                site_internet=?,
                email=?,
                phone=?,
                notes=?,
                updated_at=CURRENT_TIMESTAMP

            WHERE id=?
        """, (

            producteur.nom,
            producteur.forme_juridique,
            producteur.adresse,
            producteur.postal_code,
            producteur.city,
            producteur.siret,
            producteur.ape,
            producteur.licence,
            producteur.tva,
            producteur.iban,
            producteur.bic,
            producteur.representant,
            producteur.fonction,
            producteur.convention_collective,
            producteur.logo_path,
            producteur.site_internet,
            producteur.email,
            producteur.phone,
            producteur.notes,
            producteur.id,

        ))

    def delete(self, producteur_id: int) -> None:

        self.execute(
            "DELETE FROM producteurs WHERE id=?",
            (producteur_id,)
        )

    def deactivate_all(self) -> None:
        self.execute("UPDATE producteurs SET actif=0, updated_at=CURRENT_TIMESTAMP")

    def activate(self, producteur_id: int) -> None:
        self.execute(
            "UPDATE producteurs SET actif=1, updated_at=CURRENT_TIMESTAMP WHERE id=?",
            (producteur_id,)
        )

    def _from_row(self, row) -> Producteur:
        data = dict(row)
        data["actif"] = bool(data.get("actif"))
        return Producteur(**data)
