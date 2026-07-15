from __future__ import annotations

from typing import Any

from app.models.contract import Contract
from app.repositories.base_repository import BaseRepository


class ContractRepository(BaseRepository):
    COLUMNS = (
        "contract_number",
        "artist_id",
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
        "event_name",
        "venue",
        "event_date",
        "start_time",
        "end_time",
        "gross_salary",
        "employer_cost",
        "travel_cost",
        "accommodation_cost",
        "catering_cost",
        "comments",
        "docx_path",
        "pdf_path",
        "status",
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
        "artiste_nom",
        "artiste_adresse",
        "artiste_postal_code",
        "artiste_city",
        "artiste_phone",
        "artiste_email",
        "artiste_siren",
        "artiste_siret",
        "artiste_ape",
        "artiste_licence",
        "artiste_iban",
        "artiste_bic",
        "artiste_social_number",
        "artiste_notes",
        "spectacle_nom",
        "spectacle_duree",
        "prestation_date",
        "prestation_lieu",
        "prestation_adresse",
        "prestation_postal_code",
        "prestation_city",
        "prestation_convocation",
        "prestation_horaire",
        "cession_montant",
        "acompte",
        "cachet_tva",
        "echeance",
        "observations",
        "mode_paiement",
        "hebergement",
        "restauration",
        "kilometrage",
    )

    def get_all(self) -> list[Contract]:
        rows = self.fetch_all("""
            SELECT *
            FROM contracts
            ORDER BY created_at DESC, id DESC
        """)
        return [self._from_row(row) for row in rows]

    def get_by_id(self, contract_id: int) -> Contract | None:
        row = self.fetch_one("SELECT * FROM contracts WHERE id=?", (contract_id,))
        return self._from_row(row) if row else None

    def insert(self, contract: Contract) -> int:
        placeholders = ", ".join("?" for _ in self.COLUMNS)
        columns = ", ".join(self.COLUMNS)
        cursor = self.execute(
            f"INSERT INTO contracts({columns}) VALUES({placeholders})",
            self._params(contract),
        )
        return int(cursor.lastrowid)

    def update(self, contract: Contract) -> None:
        assignments = ", ".join(f"{column}=?" for column in self.COLUMNS)
        self.execute(
            f"""
            UPDATE contracts
            SET {assignments},
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (*self._params(contract), contract.id),
        )

    def delete(self, contract_id: int) -> None:
        self.execute("DELETE FROM contracts WHERE id=?", (contract_id,))

    def next_sequence(self, year: int) -> int:
        row = self.fetch_one(
            """
            SELECT contract_number
            FROM contracts
            WHERE contract_number LIKE ?
            ORDER BY contract_number DESC
            LIMIT 1
            """,
            (f"YGNT-{year}-%",),
        )

        if row is None or not row["contract_number"]:
            return 1

        try:
            return int(str(row["contract_number"]).split("-")[-1]) + 1
        except ValueError:
            return 1

    def mark_generated(self, contract_id: int, docx_path: str) -> None:
        self.execute(
            """
            UPDATE contracts
            SET docx_path=?,
                generated_at=CURRENT_TIMESTAMP,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (docx_path, contract_id),
        )

    def mark_pdf_exported(self, contract_id: int, pdf_path: str) -> None:
        self.execute(
            """
            UPDATE contracts
            SET pdf_path=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (pdf_path, contract_id),
        )

    def add_history(self, contract_id: int, action: str, details: str = "") -> None:
        self.execute(
            """
            INSERT INTO contract_history(contract_id, action, details)
            VALUES(?, ?, ?)
            """,
            (contract_id, action, details),
        )

    def get_history(self, contract_id: int) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            """
            SELECT action, details, created_at
            FROM contract_history
            WHERE contract_id=?
            ORDER BY created_at DESC, id DESC
            """,
            (contract_id,),
        )
        return [dict(row) for row in rows]

    def _params(self, contract: Contract) -> tuple[Any, ...]:
        return tuple(self._to_db_value(getattr(contract, column)) for column in self.COLUMNS)

    def _from_row(self, row: Any) -> Contract:
        data = dict(row)
        for key in ("hebergement", "restauration", "kilometrage"):
            data[key] = bool(data.get(key))
        return Contract(**data)

    def _to_db_value(self, value: Any) -> Any:
        if isinstance(value, bool):
            return int(value)
        return value
