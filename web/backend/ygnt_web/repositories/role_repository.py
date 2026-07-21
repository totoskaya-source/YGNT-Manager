from datetime import datetime, timezone

from ygnt_web.domain.role import Role
from ygnt_web.storage.connection import DatabaseConnection


class RoleRepository:
    def __init__(self, connection: DatabaseConnection):
        self._connection = connection

    def ajouter(
        self,
        societe_id: int,
        nom: str,
        description: str | None = None,
        permissions: tuple[str, ...] = (),
    ) -> Role:
        date_creation = datetime.now(timezone.utc)
        cursor = self._connection.execute(
            """
            INSERT INTO roles (societe_id, nom, description, date_creation)
            VALUES (?, ?, ?, ?)
            """,
            (societe_id, nom, description, date_creation.isoformat()),
        )
        role_id = cursor.lastrowid
        for permission in permissions:
            self._connection.execute(
                "INSERT INTO role_permissions (role_id, permission) VALUES (?, ?)",
                (role_id, permission),
            )
        return self.obtenir(societe_id, role_id)

    def obtenir(self, societe_id: int, role_id: int) -> Role | None:
        """Toujours filtré par Société : un Rôle d'une autre Société n'est
        jamais renvoyé, même en connaissant son identifiant exact (T4,
        isolation multi-tenant)."""
        row = self._connection.execute(
            "SELECT * FROM roles WHERE id = ? AND societe_id = ?",
            (role_id, societe_id),
        ).fetchone()
        if row is None:
            return None

        # role_id est ici garanti appartenir à societe_id (ligne ci-dessus) :
        # la lecture des permissions n'a pas besoin d'un filtre supplémentaire.
        permission_rows = self._connection.execute(
            "SELECT permission FROM role_permissions WHERE role_id = ? ORDER BY permission",
            (role_id,),
        ).fetchall()

        return Role(
            id=row["id"],
            societe_id=row["societe_id"],
            nom=row["nom"],
            description=row["description"],
            permissions=tuple(p["permission"] for p in permission_rows),
            date_creation=datetime.fromisoformat(row["date_creation"]),
        )

    def lister_par_societe(self, societe_id: int) -> list[Role]:
        rows = self._connection.execute(
            "SELECT id FROM roles WHERE societe_id = ? ORDER BY id", (societe_id,)
        ).fetchall()
        return [self.obtenir(societe_id, row["id"]) for row in rows]

    def affecter_a_utilisateur(self, societe_id: int, utilisateur_id: int, role_id: int) -> bool:
        """Garde-fou au niveau SQL (T4) : même appelée directement, sans
        passer par la vérification applicative du Service, cette méthode ne
        crée jamais une association entre un Utilisateur et un Rôle qui
        n'appartiennent pas tous les deux à `societe_id`. Renvoie False si
        l'association a été refusée (ou si elle existait déjà, ce que le
        Service ne considère pas comme une erreur puisqu'il valide les deux
        identifiants avant d'appeler cette méthode)."""
        cursor = self._connection.execute(
            """
            INSERT INTO utilisateur_roles (utilisateur_id, role_id)
            SELECT ?, ?
            WHERE EXISTS (
                SELECT 1 FROM utilisateurs WHERE id = ? AND societe_id = ?
            ) AND EXISTS (
                SELECT 1 FROM roles WHERE id = ? AND societe_id = ?
            )
            ON CONFLICT (utilisateur_id, role_id) DO NOTHING
            """,
            (utilisateur_id, role_id, utilisateur_id, societe_id, role_id, societe_id),
        )
        return cursor.rowcount > 0

    def lister_roles_utilisateur(self, societe_id: int, utilisateur_id: int) -> list[Role]:
        rows = self._connection.execute(
            """
            SELECT ur.role_id AS role_id
            FROM utilisateur_roles ur
            JOIN roles r ON r.id = ur.role_id
            WHERE ur.utilisateur_id = ? AND r.societe_id = ?
            ORDER BY ur.role_id
            """,
            (utilisateur_id, societe_id),
        ).fetchall()
        return [self.obtenir(societe_id, row["role_id"]) for row in rows]
