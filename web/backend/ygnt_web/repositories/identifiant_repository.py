from datetime import datetime, timezone

from ygnt_web.storage.connection import DatabaseConnection


class IdentifiantRepository:
    """Persiste le mot de passe (haché) d'un Utilisateur. Ne fait pas partie
    du modèle métier Utilisateur (02_DOMAIN_MODEL) : propriété interne du
    module Authentification."""

    def __init__(self, connection: DatabaseConnection):
        self._connection = connection

    def definir_mot_de_passe(
        self, societe_id: int, utilisateur_id: int, mot_de_passe_hash: str
    ) -> bool:
        """Garde-fou au niveau SQL (T4) : n'écrit jamais le mot de passe d'un
        Utilisateur qui n'appartient pas à `societe_id`, même appelée
        directement sans passer par la vérification du Service. Renvoie
        False si l'écriture a été refusée."""
        date_creation = datetime.now(timezone.utc).isoformat()
        cursor = self._connection.execute(
            """
            INSERT INTO identifiants (utilisateur_id, mot_de_passe_hash, date_creation)
            SELECT ?, ?, ?
            WHERE EXISTS (
                SELECT 1 FROM utilisateurs WHERE id = ? AND societe_id = ?
            )
            ON CONFLICT(utilisateur_id) DO UPDATE SET
                mot_de_passe_hash = excluded.mot_de_passe_hash
            """,
            (utilisateur_id, mot_de_passe_hash, date_creation, utilisateur_id, societe_id),
        )
        return cursor.rowcount > 0

    def obtenir_hash(self, utilisateur_id: int) -> str | None:
        """Non filtré par Société : n'est appelée que par le module
        Authentification juste après une résolution par email (déjà
        limitée au propre compte de l'appelant) — voir
        UtilisateurRepository.obtenir_par_email."""
        row = self._connection.execute(
            "SELECT mot_de_passe_hash FROM identifiants WHERE utilisateur_id = ?",
            (utilisateur_id,),
        ).fetchone()
        return row["mot_de_passe_hash"] if row else None
