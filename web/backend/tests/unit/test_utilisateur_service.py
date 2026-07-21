import pytest

from ygnt_web.domain.exceptions import (
    EmailDejaUtilise,
    RoleInexistant,
    SocieteInexistante,
)
from ygnt_web.domain.utilisateur import UtilisateurStatut
from ygnt_web.services.role_service import RoleService
from ygnt_web.services.societe_service import SocieteService
from ygnt_web.services.utilisateur_service import UtilisateurService


def _creer_societe_avec_role(connection, nom_societe="Acme"):
    societe = SocieteService(connection).creer_societe(nom=nom_societe)
    role = RoleService(connection).creer_role(societe_id=societe.id, nom="Producteur")
    return societe, role


def test_creer_utilisateur_assigne_le_role_fourni(connection):
    societe, role = _creer_societe_avec_role(connection)
    utilisateur_service = UtilisateurService(connection)
    role_service = RoleService(connection)

    utilisateur = utilisateur_service.creer_utilisateur(
        societe_id=societe.id,
        nom="Dupont",
        prenom="Jean",
        email="jean@acme.test",
        role_id=role.id,
    )

    roles = role_service.lister_roles_utilisateur(societe.id, utilisateur.id)

    assert utilisateur.societe_id == societe.id
    assert utilisateur.statut == UtilisateurStatut.INVITE
    assert [r.id for r in roles] == [role.id]


def test_creer_utilisateur_refuse_une_societe_inexistante(connection):
    _, role = _creer_societe_avec_role(connection)
    service = UtilisateurService(connection)

    with pytest.raises(SocieteInexistante):
        service.creer_utilisateur(
            societe_id=999,
            nom="Dupont",
            prenom="Jean",
            email="jean@acme.test",
            role_id=role.id,
        )


def test_creer_utilisateur_refuse_un_role_dune_autre_societe(connection):
    societe_a, _ = _creer_societe_avec_role(connection, "Société A")
    _, role_b = _creer_societe_avec_role(connection, "Société B")
    service = UtilisateurService(connection)

    with pytest.raises(RoleInexistant):
        service.creer_utilisateur(
            societe_id=societe_a.id,
            nom="Dupont",
            prenom="Jean",
            email="jean@a.test",
            role_id=role_b.id,
        )


def test_creer_utilisateur_refuse_un_email_deja_utilise(connection):
    societe, role = _creer_societe_avec_role(connection)
    service = UtilisateurService(connection)
    service.creer_utilisateur(
        societe_id=societe.id,
        nom="Dupont",
        prenom="Jean",
        email="jean@acme.test",
        role_id=role.id,
    )

    with pytest.raises(EmailDejaUtilise):
        service.creer_utilisateur(
            societe_id=societe.id,
            nom="Martin",
            prenom="Alice",
            email="jean@acme.test",
            role_id=role.id,
        )
