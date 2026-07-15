from __future__ import annotations

from typing import Any

from app.models.contrat_cddu import ContratCddu
from app.models.contrat_cddu_date import ContratCdduDate
from app.repositories.base_repository import BaseRepository


class ContratCdduRepository(BaseRepository):
    COLUMNS = (
        "numero",
        "prestation_id",
        "artist_id",
        "producteur_id",
        "producteur_nom",
        "producteur_forme_juridique",
        "producteur_adresse",
        "producteur_postal_code",
        "producteur_city",
        "producteur_siret",
        "producteur_ape",
        "producteur_licence",
        "producteur_convention_collective",
        "producteur_representant",
        "producteur_fonction",
        "producteur_email",
        "producteur_phone",
        "artiste_nom",
        "artiste_prenom",
        "artiste_adresse",
        "artiste_postal_code",
        "artiste_city",
        "artiste_phone",
        "artiste_email",
        "artiste_date_naissance",
        "artiste_lieu_naissance",
        "artiste_numero_secu",
        "artiste_numero_conges_spectacle",
        "artiste_fonction",
        "artiste_qualification",
        "prestation_reference",
        "prestation_objet",
        "prestation_lieu",
        "prestation_ville",
        "numero_objet",
        "remuneration_brute",
        "defraiement_deplacement",
        "defraiement_hebergement",
        "defraiement_repas",
        "defraiement_autres_libelle",
        "defraiement_autres_montant",
        "defraiement_montant_libre_libelle",
        "defraiement_montant_libre_montant",
        "observations",
        "ville_signature",
        "date_signature",
        "docx_path",
        "pdf_path",
        "status",
    )

    # ===== contrats_cddu =====

    def get_all(self) -> list[ContratCddu]:
        rows = self.fetch_all("""
            SELECT *
            FROM contrats_cddu
            ORDER BY created_at DESC, id DESC
        """)
        return [self._from_row(row) for row in rows]

    def get_by_id(self, contrat_id: int) -> ContratCddu | None:
        row = self.fetch_one("SELECT * FROM contrats_cddu WHERE id=?", (contrat_id,))
        return self._from_row(row) if row else None

    def insert(self, contrat: ContratCddu) -> int:
        placeholders = ", ".join("?" for _ in self.COLUMNS)
        columns = ", ".join(self.COLUMNS)
        cursor = self.execute(
            f"INSERT INTO contrats_cddu({columns}) VALUES({placeholders})",
            self._params(contrat),
        )
        return int(cursor.lastrowid)

    def update(self, contrat: ContratCddu) -> None:
        assignments = ", ".join(f"{column}=?" for column in self.COLUMNS)
        self.execute(
            f"""
            UPDATE contrats_cddu
            SET {assignments},
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (*self._params(contrat), contrat.id),
        )

    def delete(self, contrat_id: int) -> None:
        self.execute("DELETE FROM contrats_cddu WHERE id=?", (contrat_id,))

    def next_sequence(self, year: int) -> int:
        row = self.fetch_one(
            """
            SELECT numero
            FROM contrats_cddu
            WHERE numero LIKE ?
            ORDER BY numero DESC
            LIMIT 1
            """,
            (f"CDDU-{year}-%",),
        )

        if row is None or not row["numero"]:
            return 1

        try:
            return int(str(row["numero"]).split("-")[-1]) + 1
        except ValueError:
            return 1

    def mark_generated(self, contrat_id: int, docx_path: str) -> None:
        self.execute(
            """
            UPDATE contrats_cddu
            SET docx_path=?,
                generated_at=CURRENT_TIMESTAMP,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (docx_path, contrat_id),
        )

    def mark_pdf_exported(self, contrat_id: int, pdf_path: str) -> None:
        self.execute(
            """
            UPDATE contrats_cddu
            SET pdf_path=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (pdf_path, contrat_id),
        )

    def set_status(self, contrat_id: int, status: str) -> None:
        self.execute(
            """
            UPDATE contrats_cddu
            SET status=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (status, contrat_id),
        )

    def set_signature_defaults(self, contrat_id: int, ville_signature: str, date_signature: str) -> None:
        self.execute(
            """
            UPDATE contrats_cddu
            SET ville_signature=?,
                date_signature=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (ville_signature, date_signature, contrat_id),
        )

    def add_history(self, contrat_id: int, action: str, details: str = "") -> None:
        self.execute(
            """
            INSERT INTO contrat_cddu_history(contrat_cddu_id, action, details)
            VALUES(?, ?, ?)
            """,
            (contrat_id, action, details),
        )

    def get_history(self, contrat_id: int) -> list[dict[str, Any]]:
        rows = self.fetch_all(
            """
            SELECT action, details, created_at
            FROM contrat_cddu_history
            WHERE contrat_cddu_id=?
            ORDER BY created_at DESC, id DESC
            """,
            (contrat_id,),
        )
        return [dict(row) for row in rows]

    def _params(self, contrat: ContratCddu) -> tuple[Any, ...]:
        return tuple(getattr(contrat, column) for column in self.COLUMNS)

    def _from_row(self, row: Any) -> ContratCddu:
        return ContratCddu(**dict(row))

    # ===== contrat_cddu_dates =====
    # Simple plomberie de stockage pour ce sprint : aucune regle metier
    # (exclusion des dates deja contractualisees, recherche "toutes les
    # prestations du mois"...) n'est implementee ici, voir
    # docs/CDDU_ARCHITECTURE.md §7 pour le comportement prevu cote UI.

    def add_date(self, date: ContratCdduDate) -> int:
        cursor = self.execute(
            """
            INSERT INTO contrat_cddu_dates(contrat_cddu_id, prestation_id, date_travaillee, nombre_cachets)
            VALUES(?, ?, ?, ?)
            """,
            (date.contrat_cddu_id, date.prestation_id, date.date_travaillee, date.nombre_cachets),
        )
        return int(cursor.lastrowid)

    def list_dates(self, contrat_id: int) -> list[ContratCdduDate]:
        rows = self.fetch_all(
            """
            SELECT *
            FROM contrat_cddu_dates
            WHERE contrat_cddu_id=?
            ORDER BY date_travaillee ASC, id ASC
            """,
            (contrat_id,),
        )
        return [ContratCdduDate(**dict(row)) for row in rows]

    def delete_date(self, date_id: int) -> None:
        self.execute("DELETE FROM contrat_cddu_dates WHERE id=?", (date_id,))

    def delete_dates_for_contract(self, contrat_id: int) -> None:
        self.execute("DELETE FROM contrat_cddu_dates WHERE contrat_cddu_id=?", (contrat_id,))

    def contrat_ids_for_prestation_dates(self, prestation_id: int) -> list[int]:
        """Identifiants des CDDU couvrant reellement cette prestation via au
        moins une ligne contrat_cddu_dates - une seule requete SQL, source de
        verite du rattachement pour un CDDU mensualise."""
        rows = self.fetch_all(
            """
            SELECT DISTINCT contrat_cddu_id
            FROM contrat_cddu_dates
            WHERE prestation_id=?
            """,
            (prestation_id,),
        )
        return [int(row["contrat_cddu_id"]) for row in rows]
