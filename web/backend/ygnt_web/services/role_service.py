from ygnt_web.domain.exceptions import (
    NomRoleObligatoire,
    RoleInexistant,
    SocieteInexistante,
    UtilisateurInexistant,
)
from ygnt_web.domain.role import Role
from ygnt_web.repositories.role_repository import RoleRepository
from ygnt_web.repositories.societe_repository import SocieteRepository
from ygnt_web.repositories.utilisateur_repository import UtilisateurRepository
from ygnt_web.storage.connection import DatabaseConnection


class RoleService:
    def __init__(self, connection: DatabaseConnection):
        self._roles = RoleRepository(connection)
        self._societes = SocieteRepository(connection)
        self._utilisateurs = UtilisateurRepository(connection)

    def creer_role(
        self,
        societe_id: int,
        nom: str,
        description: str | None = None,
        permissions: tuple[str, ...] = (),
    ) -> Role:
        if self._societes.obtenir(societe_id) is None:
            raise SocieteInexistante(societe_id)
        if not nom or not nom.strip():
            raise NomRoleObligatoire()

        return self._roles.ajouter(
            societe_id=societe_id,
            nom=nom.strip(),
            description=description,
            permissions=tuple(permissions),
        )

    def affecter_role(self, societe_id: int, utilisateur_id: int, role_id: int) -> None:
        """`societe_id` est le tenant du contexte authentifié de l'appelant
        (jamais transmis par le Frontend) : Utilisateur et Rôle sont tous
        deux résolus filtrés par cette même Société (T4). Un Rôle ou un
        Utilisateur d'une autre Société est traité exactement comme un
        identifiant inexistant — jamais distingué par un message d'erreur
        différent, pour ne pas révéler l'existence d'une ressource hors
        tenant."""
        utilisateur = self._utilisateurs.obtenir(societe_id, utilisateur_id)
        if utilisateur is None:
            raise UtilisateurInexistant(utilisateur_id)

        role = self._roles.obtenir(societe_id, role_id)
        if role is None:
            raise RoleInexistant(role_id)

        self._roles.affecter_a_utilisateur(societe_id, utilisateur_id, role_id)

    def lister_roles_utilisateur(self, societe_id: int, utilisateur_id: int) -> list[Role]:
        if self._utilisateurs.obtenir(societe_id, utilisateur_id) is None:
            raise UtilisateurInexistant(utilisateur_id)
        return self._roles.lister_roles_utilisateur(societe_id, utilisateur_id)
