from datetime import datetime, timezone
from typing import Any

from ygnt_web.domain.utilisateur import Utilisateur, UtilisateurStatut
from ygnt_web.storage.connection import DatabaseConnection


def _row_to_utilisateur(row: Any) -> Utilisateur:
    return Utilisateur(
        id=row["id"],
        societe_id=row["societe_id"],
        nom=row["nom"],
        prenom=row["prenom"],
        email=row["email"],
        statut=UtilisateurStatut(row["statut"]),
        date_creation=datetime.fromisoformat(row["date_creation"]),
    )


class UtilisateurRepository:
    def __init__(self, connection: DatabaseConnection):
        self._connection = connection

    def ajouter(self, societe_id: int, nom: str, prenom: str, email: str) -> Utilisateur:
        date_creation = datetime.now(timezone.utc)
        cursor = self._connection.execute(
            """
            INSERT INTO utilisateurs (
                societe_id, nom, prenom, email, statut, date_creation
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                societe_id,
                nom,
                prenom,
                email,
                UtilisateurStatut.INVITE.value,
                date_creation.isoformat(),
            ),
        )
        return self.obtenir(societe_id, cursor.lastrowid)

    def obtenir(self, societe_id: int, utilisateur_id: int) -> Utilisateur | None:
        """Toujours filtré par Société : un Utilisateur d'une autre Société
        n'est jamais renvoyé, même en connaissant son identifiant exact
        (T4, isolation multi-tenant)."""
        row = self._connection.execute(
            "SELECT * FROM utilisateurs WHERE id = ? AND societe_id = ?",
            (utilisateur_id, societe_id),
        ).fetchone()
        return _row_to_utilisateur(row) if row else None

    def obtenir_par_email(self, email: str) -> Utilisateur | None:
        """Seule lecture non filtrée par Société de ce Repository : nécessaire
        à la connexion (l'Utilisateur ne connaît pas encore sa Société au
        moment de s'identifier par email). N'est appelée que par le module
        Authentification, jamais avec une valeur devinée ou fournie par une
        autre Société — le résultat ne peut être que le propre compte de la
        personne qui possède cet email."""
        row = self._connection.execute(
            "SELECT * FROM utilisateurs WHERE email = ?", (email,)
        ).fetchone()
        return _row_to_utilisateur(row) if row else None

    def lister_par_societe(self, societe_id: int) -> list[Utilisateur]:
        rows = self._connection.execute(
            "SELECT * FROM utilisateurs WHERE societe_id = ? ORDER BY id",
            (societe_id,),
        ).fetchall()
        return [_row_to_utilisateur(row) for row in rows]
