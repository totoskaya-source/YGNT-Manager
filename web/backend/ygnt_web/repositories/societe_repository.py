from datetime import datetime, timezone
from typing import Any

from ygnt_web.domain.societe import Societe, SocieteStatut
from ygnt_web.storage.connection import DatabaseConnection


def _row_to_societe(row: Any) -> Societe:
    return Societe(
        id=row["id"],
        nom=row["nom"],
        forme_juridique=row["forme_juridique"],
        siret=row["siret"],
        adresse=row["adresse"],
        code_postal=row["code_postal"],
        ville=row["ville"],
        email_contact=row["email_contact"],
        statut=SocieteStatut(row["statut"]),
        date_creation=datetime.fromisoformat(row["date_creation"]),
    )


class SocieteRepository:
    def __init__(self, connection: DatabaseConnection):
        self._connection = connection

    def ajouter(
        self,
        nom: str,
        forme_juridique: str | None = None,
        siret: str | None = None,
        adresse: str | None = None,
        code_postal: str | None = None,
        ville: str | None = None,
        email_contact: str | None = None,
    ) -> Societe:
        date_creation = datetime.now(timezone.utc)
        cursor = self._connection.execute(
            """
            INSERT INTO societes (
                nom, forme_juridique, siret, adresse, code_postal, ville,
                email_contact, statut, date_creation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                nom,
                forme_juridique,
                siret,
                adresse,
                code_postal,
                ville,
                email_contact,
                SocieteStatut.ACTIVE.value,
                date_creation.isoformat(),
            ),
        )
        return self.obtenir(cursor.lastrowid)

    def obtenir(self, societe_id: int) -> Societe | None:
        row = self._connection.execute(
            "SELECT * FROM societes WHERE id = ?", (societe_id,)
        ).fetchone()
        return _row_to_societe(row) if row else None
