from __future__ import annotations

from typing import Any

from app.models.devis import Devis
from app.repositories.base_repository import BaseRepository


class DevisRepository(BaseRepository):
    COLUMNS = (
        "devis_number",
        "formation_id",
        "organization_id",
        "prestation_id",
        "producteur_id",
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
        "acompte",
        "tva",
        "mode_paiement",
        "echeance",
        "date_validite",
        "observations",
        "comments",
        "hebergement",
        "restauration",
        "kilometrage",
        "docx_path",
        "pdf_path",
        "status",
    )

    def get_all(self) -> list[Devis]:
        rows = self.fetch_all("""
            SELECT *
            FROM devis
            ORDER BY created_at DESC, id DESC
        """)
        return [self._from_row(row) for row in rows]

    def get_by_id(self, devis_id: int) -> Devis | None:
        row = self.fetch_one("SELECT * FROM devis WHERE id=?", (devis_id,))
        return self._from_row(row) if row else None

    def insert(self, devis: Devis) -> int:
        placeholders = ", ".join("?" for _ in self.COLUMNS)
        columns = ", ".join(self.COLUMNS)
        cursor = self.execute(
            f"INSERT INTO devis({columns}) VALUES({placeholders})",
            self._params(devis),
        )
        return int(cursor.lastrowid)

    def update(self, devis: Devis) -> None:
        assignments = ", ".join(f"{column}=?" for column in self.COLUMNS)
        self.execute(
            f"""
            UPDATE devis
            SET {assignments},
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (*self._params(devis), devis.id),
        )

    def delete(self, devis_id: int) -> None:
        self.execute("DELETE FROM devis WHERE id=?", (devis_id,))

    def next_sequence(self, year: int) -> int:
        row = self.fetch_one(
            """
            SELECT devis_number
            FROM devis
            WHERE devis_number LIKE ?
            ORDER BY devis_number DESC
            LIMIT 1
            """,
            (f"DEVIS-{year}-%",),
        )

        if row is None or not row["devis_number"]:
            return 1

        try:
            return int(str(row["devis_number"]).split("-")[-1]) + 1
        except ValueError:
            return 1

    def mark_generated(self, devis_id: int, docx_path: str) -> None:
        self.execute(
            """
            UPDATE devis
            SET docx_path=?,
                generated_at=CURRENT_TIMESTAMP,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (docx_path, devis_id),
        )

    def mark_pdf_exported(self, devis_id: int, pdf_path: str) -> None:
        self.execute(
            """
            UPDATE devis
            SET pdf_path=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (pdf_path, devis_id),
        )

    def _params(self, devis: Devis) -> tuple[Any, ...]:
        return tuple(self._to_db_value(getattr(devis, column)) for column in self.COLUMNS)

    def _from_row(self, row: Any) -> Devis:
        data = dict(row)
        for key in ("hebergement", "restauration", "kilometrage"):
            data[key] = bool(data.get(key))
        return Devis(**data)

    def _to_db_value(self, value: Any) -> Any:
        if isinstance(value, bool):
            return int(value)
        return value
