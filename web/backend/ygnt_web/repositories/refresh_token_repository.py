from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from ygnt_web.storage.connection import DatabaseConnection


@dataclass(frozen=True)
class RefreshTokenEnregistre:
    utilisateur_id: int
    societe_id: int
    token_hash: str


class RefreshTokenRepository:
    def __init__(self, connection: DatabaseConnection):
        self._connection = connection

    def creer(
        self, utilisateur_id: int, societe_id: int, token_hash: str, duree_secondes: int
    ) -> None:
        maintenant = datetime.now(timezone.utc)
        expiration = maintenant + timedelta(seconds=duree_secondes)
        self._connection.execute(
            """
            INSERT INTO refresh_tokens (
                utilisateur_id, societe_id, token_hash, date_creation, date_expiration
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                utilisateur_id,
                societe_id,
                token_hash,
                maintenant.isoformat(),
                expiration.isoformat(),
            ),
        )

    def obtenir_valide(self, token_hash: str) -> RefreshTokenEnregistre | None:
        """Non filtré par Société : un jeton de rafraîchissement est un
        secret porteur (bearer) — sa seule connaissance identifie déjà de
        façon univoque son propriétaire, avant même qu'un contexte de
        Société n'existe. societe_id est lu depuis l'enregistrement
        lui-même (dénormalisé à l'émission), jamais recalculé à partir d'une
        entrée cliente."""
        row = self._connection.execute(
            "SELECT * FROM refresh_tokens WHERE token_hash = ?", (token_hash,)
        ).fetchone()
        if row is None or row["revoque_le"] is not None:
            return None
        if datetime.fromisoformat(row["date_expiration"]) < datetime.now(timezone.utc):
            return None
        return RefreshTokenEnregistre(
            utilisateur_id=row["utilisateur_id"],
            societe_id=row["societe_id"],
            token_hash=row["token_hash"],
        )

    def revoquer(self, token_hash: str) -> None:
        self._connection.execute(
            "UPDATE refresh_tokens SET revoque_le = ? WHERE token_hash = ?",
            (datetime.now(timezone.utc).isoformat(), token_hash),
        )
