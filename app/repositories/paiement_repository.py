from __future__ import annotations

from typing import Any

from app.models.paiement import Paiement
from app.repositories.base_repository import BaseRepository


class PaiementRepository(BaseRepository):
    COLUMNS = (
        "reference",
        "facture_id",
        "date_paiement",
        "montant",
        "mode_paiement",
        "reference_bancaire",
        "observations",
        "status",
    )

    def get_all(self) -> list[Paiement]:
        rows = self.fetch_all("""
            SELECT *
            FROM paiements
            ORDER BY created_at DESC, id DESC
        """)
        return [self._from_row(row) for row in rows]

    def get_by_id(self, paiement_id: int) -> Paiement | None:
        row = self.fetch_one("SELECT * FROM paiements WHERE id=?", (paiement_id,))
        return self._from_row(row) if row else None

    def get_for_facture(self, facture_id: int) -> list[Paiement]:
        """Un paiement appartient toujours a une facture (FK obligatoire) :
        contrairement a prestation_id sur Devis/Facture (relation optionnelle
        filtree en memoire), cette relation est la relation primaire du
        modele et merite une requete SQL dediee."""
        rows = self.fetch_all(
            """
            SELECT *
            FROM paiements
            WHERE facture_id=?
            ORDER BY created_at DESC, id DESC
            """,
            (facture_id,),
        )
        return [self._from_row(row) for row in rows]

    def insert(self, paiement: Paiement) -> int:
        placeholders = ", ".join("?" for _ in self.COLUMNS)
        columns = ", ".join(self.COLUMNS)
        cursor = self.execute(
            f"INSERT INTO paiements({columns}) VALUES({placeholders})",
            self._params(paiement),
        )
        return int(cursor.lastrowid)

    def update(self, paiement: Paiement) -> None:
        assignments = ", ".join(f"{column}=?" for column in self.COLUMNS)
        self.execute(
            f"""
            UPDATE paiements
            SET {assignments},
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (*self._params(paiement), paiement.id),
        )

    def delete(self, paiement_id: int) -> None:
        self.execute("DELETE FROM paiements WHERE id=?", (paiement_id,))

    def next_sequence(self, year: int) -> int:
        row = self.fetch_one(
            """
            SELECT reference
            FROM paiements
            WHERE reference LIKE ?
            ORDER BY reference DESC
            LIMIT 1
            """,
            (f"PAI-{year}-%",),
        )

        if row is None or not row["reference"]:
            return 1

        try:
            return int(str(row["reference"]).split("-")[-1]) + 1
        except ValueError:
            return 1

    def _params(self, paiement: Paiement) -> tuple[Any, ...]:
        return tuple(self._to_db_value(getattr(paiement, column)) for column in self.COLUMNS)

    def _from_row(self, row: Any) -> Paiement:
        data = dict(row)
        return Paiement(**data)

    def _to_db_value(self, value: Any) -> Any:
        if isinstance(value, bool):
            return int(value)
        return value
