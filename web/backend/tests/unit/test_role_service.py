import pytest

from ygnt_web.domain.exceptions import NomRoleObligatoire, RoleInexistant
from ygnt_web.services.role_service import RoleService
from ygnt_web.services.societe_service import SocieteService
from ygnt_web.services.utilisateur_service import UtilisateurService


def test_creer_role_rattache_a_une_societe(connection):
    societe = SocieteService(connection).creer_societe(nom="Acme")
    role_service = RoleService(connection)

    role = role_service.creer_role(
        societe_id=societe.id, nom="Producteur", permissions=("prestations.gerer",)
    )

    assert role.societe_id == societe.id
    assert role.permissions == ("prestations.gerer",)


def test_creer_role_sans_nom_leve_une_erreur(connection):
    societe = SocieteService(connection).creer_societe(nom="Acme")
    role_service = RoleService(connection)

    with pytest.raises(NomRoleObligatoire):
        role_service.creer_role(societe_id=societe.id, nom="   ")


def test_affecter_role_refuse_entre_societes_differentes(connection):
    societe_service = SocieteService(connection)
    role_service = RoleService(connection)
    utilisateur_service = UtilisateurService(connection)

    societe_a = societe_service.creer_societe(nom="Société A")
    societe_b = societe_service.creer_societe(nom="Société B")

    role_a = role_service.creer_role(societe_id=societe_a.id, nom="Producteur")
    role_b = role_service.creer_role(societe_id=societe_b.id, nom="Collaborateur")

    utilisateur_b = utilisateur_service.creer_utilisateur(
        societe_id=societe_b.id,
        nom="Dupont",
        prenom="Jean",
        email="jean@b.test",
        role_id=role_b.id,
    )

    with pytest.raises(RoleInexistant):
        role_service.affecter_role(
            societe_id=societe_b.id, utilisateur_id=utilisateur_b.id, role_id=role_a.id
        )
