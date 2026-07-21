"""Tests de sécurité (T4) : simulent deux scénarios d'intrusion.

1. Un bug applicatif qui oublierait la vérification de tenant côté Service —
   les Repositories sont attaqués directement, avec des identifiants
   incohérents entre eux, pour prouver que le garde-fou SQL tient tout seul.
2. Un attaquant authentifié dans une Société qui tente d'agir sur les
   ressources d'une autre Société via les Services, avec son propre
   contexte valide mais des identifiants de ressources devinés/empruntés.

Aucune route API n'expose encore de ressource par identifiant (T4 interdit
toute API métier) : les intrusions plausibles à ce stade se jouent au
niveau Repository/Service, pas HTTP — voir tests/integration/test_auth_flow.py
pour la vérification (déjà couverte) qu'un jeton falsifié est rejeté.
"""

import pytest

from ygnt_web.domain.exceptions import RoleInexistant, UtilisateurInexistant
from ygnt_web.repositories.identifiant_repository import IdentifiantRepository
from ygnt_web.repositories.role_repository import RoleRepository
from ygnt_web.repositories.utilisateur_repository import UtilisateurRepository
from ygnt_web.services.auth_service import AuthService
from ygnt_web.services.role_service import RoleService
from ygnt_web.services.societe_service import SocieteService
from ygnt_web.services.utilisateur_service import UtilisateurService


def _deux_societes_avec_role_et_utilisateur(connection):
    societe_a = SocieteService(connection).creer_societe(nom="Société A")
    societe_b = SocieteService(connection).creer_societe(nom="Société B")

    role_a = RoleService(connection).creer_role(societe_id=societe_a.id, nom="Producteur")
    role_b = RoleService(connection).creer_role(societe_id=societe_b.id, nom="Collaborateur")

    utilisateur_a = UtilisateurService(connection).creer_utilisateur(
        societe_id=societe_a.id, nom="Dupont", prenom="Jean", email="jean@a.test", role_id=role_a.id
    )
    utilisateur_b = UtilisateurService(connection).creer_utilisateur(
        societe_id=societe_b.id, nom="Martin", prenom="Alice", email="alice@b.test", role_id=role_b.id
    )
    return societe_a, societe_b, role_a, role_b, utilisateur_a, utilisateur_b


# --- 1. Intrusions directes au niveau Repository (contournement du Service) ---


def test_utilisateur_repository_ne_renvoie_rien_hors_de_sa_societe(connection):
    societe_a, societe_b, _, _, utilisateur_a, _ = _deux_societes_avec_role_et_utilisateur(
        connection
    )
    repository = UtilisateurRepository(connection)

    assert repository.obtenir(societe_b.id, utilisateur_a.id) is None
    assert repository.obtenir(societe_a.id, utilisateur_a.id) is not None


def test_role_repository_ne_renvoie_rien_hors_de_sa_societe(connection):
    societe_a, societe_b, role_a, _, _, _ = _deux_societes_avec_role_et_utilisateur(connection)
    repository = RoleRepository(connection)

    assert repository.obtenir(societe_b.id, role_a.id) is None
    assert repository.obtenir(societe_a.id, role_a.id) is not None


def test_affecter_a_utilisateur_refuse_une_association_croisee_au_niveau_sql(connection):
    societe_a, societe_b, role_a, role_b, _, utilisateur_b = _deux_societes_avec_role_et_utilisateur(
        connection
    )
    repository = RoleRepository(connection)

    # Appel direct, société_id ne correspondant ni au propriétaire réel de
    # utilisateur_b (societe_b) ni à celui de role_a (societe_a) : simule un
    # Service qui aurait oublié de valider en amont.
    reussi = repository.affecter_a_utilisateur(
        societe_id=societe_a.id, utilisateur_id=utilisateur_b.id, role_id=role_a.id
    )

    assert reussi is False
    roles_de_utilisateur_b = repository.lister_roles_utilisateur(societe_b.id, utilisateur_b.id)
    # utilisateur_b garde uniquement son Rôle légitime (role_b, affecté à sa
    # création) : role_a n'a jamais été ajouté.
    assert [r.id for r in roles_de_utilisateur_b] == [role_b.id]


def test_definir_mot_de_passe_refuse_un_utilisateur_hors_societe_au_niveau_sql(connection):
    societe_a, societe_b, _, _, utilisateur_a, _ = _deux_societes_avec_role_et_utilisateur(
        connection
    )
    repository = IdentifiantRepository(connection)

    reussi = repository.definir_mot_de_passe(societe_b.id, utilisateur_a.id, "hash-quelconque")

    assert reussi is False
    assert repository.obtenir_hash(utilisateur_a.id) is None


# --- 2. Intrusions via les Services, avec un contexte de tenant valide ---


def test_role_service_affecter_role_refuse_un_role_dune_autre_societe(connection):
    societe_a, societe_b, role_a, _, _, utilisateur_b = _deux_societes_avec_role_et_utilisateur(
        connection
    )
    service = RoleService(connection)

    with pytest.raises(RoleInexistant):
        service.affecter_role(
            societe_id=societe_b.id, utilisateur_id=utilisateur_b.id, role_id=role_a.id
        )


def test_role_service_affecter_role_refuse_un_utilisateur_dune_autre_societe(connection):
    societe_a, societe_b, _, role_b, utilisateur_a, _ = _deux_societes_avec_role_et_utilisateur(
        connection
    )
    service = RoleService(connection)

    with pytest.raises(UtilisateurInexistant):
        service.affecter_role(
            societe_id=societe_b.id, utilisateur_id=utilisateur_a.id, role_id=role_b.id
        )


def test_auth_service_definir_mot_de_passe_refuse_un_utilisateur_dune_autre_societe(connection):
    societe_a, societe_b, _, _, utilisateur_a, _ = _deux_societes_avec_role_et_utilisateur(
        connection
    )
    service = AuthService(connection)

    with pytest.raises(UtilisateurInexistant):
        service.definir_mot_de_passe(societe_b.id, utilisateur_a.id, "mot-de-passe-attaquant")

    assert IdentifiantRepository(connection).obtenir_hash(utilisateur_a.id) is None


# --- 3. Non-distinction entre "inexistant" et "existe ailleurs" ---


def test_role_inexistant_et_role_dune_autre_societe_produisent_la_meme_erreur(connection):
    societe_a, societe_b, _, role_b, _, _ = _deux_societes_avec_role_et_utilisateur(connection)
    service = UtilisateurService(connection)

    with pytest.raises(RoleInexistant) as leve_pour_role_etranger:
        service.creer_utilisateur(
            societe_id=societe_a.id,
            nom="X",
            prenom="Y",
            email="x1@a.test",
            role_id=role_b.id,
        )

    with pytest.raises(RoleInexistant) as leve_pour_role_absent:
        service.creer_utilisateur(
            societe_id=societe_a.id,
            nom="X",
            prenom="Y",
            email="x2@a.test",
            role_id=999_999,
        )

    assert type(leve_pour_role_etranger.value) is type(leve_pour_role_absent.value)
