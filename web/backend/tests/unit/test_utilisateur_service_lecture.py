import pytest

from ygnt_web.domain.exceptions import UtilisateurInexistant
from ygnt_web.services.role_service import RoleService
from ygnt_web.services.societe_service import SocieteService
from ygnt_web.services.utilisateur_service import UtilisateurService


def test_obtenir_utilisateur_renvoie_la_fiche(connection):
    societe = SocieteService(connection).creer_societe(nom="Acme")
    role = RoleService(connection).creer_role(societe_id=societe.id, nom="Producteur")
    service = UtilisateurService(connection)
    cree = service.creer_utilisateur(
        societe_id=societe.id, nom="Dupont", prenom="Jean", email="jean@acme.test", role_id=role.id
    )

    utilisateur = service.obtenir_utilisateur(societe.id, cree.id)

    assert utilisateur.nom == "Dupont"
    assert utilisateur.prenom == "Jean"


def test_obtenir_utilisateur_dune_autre_societe_leve_utilisateur_inexistant(connection):
    societe_a = SocieteService(connection).creer_societe(nom="Société A")
    societe_b = SocieteService(connection).creer_societe(nom="Société B")
    role_b = RoleService(connection).creer_role(societe_id=societe_b.id, nom="Producteur")
    utilisateur_b = UtilisateurService(connection).creer_utilisateur(
        societe_id=societe_b.id, nom="Martin", prenom="Alice", email="alice@b.test", role_id=role_b.id
    )

    with pytest.raises(UtilisateurInexistant):
        UtilisateurService(connection).obtenir_utilisateur(societe_a.id, utilisateur_b.id)
