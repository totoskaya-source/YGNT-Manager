from ygnt_web.domain.exceptions import (
    EmailDejaUtilise,
    RoleInexistant,
    SocieteInexistante,
    UtilisateurInexistant,
)
from ygnt_web.domain.utilisateur import Utilisateur
from ygnt_web.repositories.role_repository import RoleRepository
from ygnt_web.repositories.societe_repository import SocieteRepository
from ygnt_web.repositories.utilisateur_repository import UtilisateurRepository
from ygnt_web.storage.connection import DatabaseConnection


class UtilisateurService:
    def __init__(self, connection: DatabaseConnection):
        self._utilisateurs = UtilisateurRepository(connection)
        self._societes = SocieteRepository(connection)
        self._roles = RoleRepository(connection)

    def creer_utilisateur(
        self, societe_id: int, nom: str, prenom: str, email: str, role_id: int
    ) -> Utilisateur:
        """Crée un Utilisateur et lui affecte immédiatement son Rôle initial :
        un Utilisateur possède toujours au moins un Rôle (02_DOMAIN_MODEL §3.2),
        jamais un état transitoire sans Rôle.

        `role_id` est résolu via une lecture filtrée par `societe_id` (T4) :
        un Rôle d'une autre Société est structurellement introuvable ici,
        indiscernable d'un identifiant qui n'existe pas du tout — aucune
        des deux situations ne doit renseigner l'appelant sur l'existence
        d'une ressource appartenant à une autre Société."""
        if self._societes.obtenir(societe_id) is None:
            raise SocieteInexistante(societe_id)

        role = self._roles.obtenir(societe_id, role_id)
        if role is None:
            raise RoleInexistant(role_id)

        if self._utilisateurs.obtenir_par_email(email) is not None:
            raise EmailDejaUtilise(email)

        utilisateur = self._utilisateurs.ajouter(
            societe_id=societe_id, nom=nom, prenom=prenom, email=email
        )
        self._roles.affecter_a_utilisateur(societe_id, utilisateur.id, role_id)
        return utilisateur

    def obtenir_utilisateur(self, societe_id: int, utilisateur_id: int) -> Utilisateur:
        utilisateur = self._utilisateurs.obtenir(societe_id, utilisateur_id)
        if utilisateur is None:
            raise UtilisateurInexistant(utilisateur_id)
        return utilisateur
