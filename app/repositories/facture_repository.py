from __future__ import annotations

from typing import Any

from app.models.facture import Facture
from app.repositories.base_repository import BaseRepository


class FactureRepository(BaseRepository):
    COLUMNS = (
        "facture_number",
        "prestation_id",
        "contract_id",
        "producteur_id",
        "formation_id",
        "organization_id",
        "producteur_nom",
        "producteur_forme_juridique",
        "producteur_adresse",
        "producteur_code_postal",
        "producteur_ville",
        "producteur_siret",
        "producteur_ape",
        "producteur_licence",
        "producteur_tva_intracommunautaire",
        "producteur_telephone",
        "producteur_email",
        "producteur_site",
        "producteur_representant",
        "producteur_fonction",
        "producteur_iban",
        "producteur_bic",
        "producteur_logo_path",
        "organisateur_structure",
        "organisateur_forme",
        "organisateur_adresse",
        "organisateur_postal_code",
        "organisateur_city",
        "organisateur_siret",
        "organisateur_phone",
        "organisateur_email",
        "organisateur_ape",
        "organisateur_licence",
        "organisateur_tva",
        "organisateur_representant",
        "organisateur_fonction",
        "organisateur_iban",
        "organisateur_bic",
        "organisateur_site_internet",
        "organisateur_notes",
        "formation_nom",
        "formation_adresse",
        "formation_postal_code",
        "formation_city",
        "formation_phone",
        "formation_email",
        "formation_site_internet",
        "formation_siren",
        "formation_siret",
        "formation_ape",
        "formation_licence",
        "formation_iban",
        "formation_bic",
        "formation_social_number",
        "formation_notes",
        "spectacle_nom",
        "spectacle_duree",
        "prestation_date",
        "prestation_lieu",
        "prestation_adresse",
        "prestation_postal_code",
        "prestation_city",
        "prestation_convocation",
        "prestation_horaire",
        "montant",
        "tva",
        "acompte",
        "total",
        "mode_paiement",
        "echeance",
        "observations",
        "comments",
        "docx_path",
        "pdf_path",
        "status",
    )

    def get_all(self) -> list[Facture]:
        rows = self.fetch_all("""
            SELECT *
            FROM factures
            ORDER BY created_at DESC, id DESC
        """)
        return [self._from_row(row) for row in rows]

    def get_by_id(self, facture_id: int) -> Facture | None:
        row = self.fetch_one("SELECT * FROM factures WHERE id=?", (facture_id,))
        return self._from_row(row) if row else None

    def insert(self, facture: Facture) -> int:
        placeholders = ", ".join("?" for _ in self.COLUMNS)
        columns = ", ".join(self.COLUMNS)
        cursor = self.execute(
            f"INSERT INTO factures({columns}) VALUES({placeholders})",
            self._params(facture),
        )
        return int(cursor.lastrowid)

    def update(self, facture: Facture) -> None:
        assignments = ", ".join(f"{column}=?" for column in self.COLUMNS)
        self.execute(
            f"""
            UPDATE factures
            SET {assignments},
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (*self._params(facture), facture.id),
        )

    def delete(self, facture_id: int) -> None:
        self.execute("DELETE FROM factures WHERE id=?", (facture_id,))

    def next_sequence(self, year: int) -> int:
        row = self.fetch_one(
            """
            SELECT facture_number
            FROM factures
            WHERE facture_number LIKE ?
            ORDER BY facture_number DESC
            LIMIT 1
            """,
            (f"FACT-{year}-%",),
        )

        if row is None or not row["facture_number"]:
            return 1

        try:
            return int(str(row["facture_number"]).split("-")[-1]) + 1
        except ValueError:
            return 1

    def mark_generated(self, facture_id: int, docx_path: str) -> None:
        self.execute(
            """
            UPDATE factures
            SET docx_path=?,
                generated_at=CURRENT_TIMESTAMP,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (docx_path, facture_id),
        )

    def mark_pdf_exported(self, facture_id: int, pdf_path: str) -> None:
        self.execute(
            """
            UPDATE factures
            SET pdf_path=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (pdf_path, facture_id),
        )

    def update_status(self, facture_id: int, status: str) -> None:
        self.execute(
            """
            UPDATE factures
            SET status=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (status, facture_id),
        )

    def _params(self, facture: Facture) -> tuple[Any, ...]:
        return tuple(self._to_db_value(getattr(facture, column)) for column in self.COLUMNS)

    def _from_row(self, row: Any) -> Facture:
        data = dict(row)
        return Facture(**data)

    def _to_db_value(self, value: Any) -> Any:
        if isinstance(value, bool):
            return int(value)
        return value
