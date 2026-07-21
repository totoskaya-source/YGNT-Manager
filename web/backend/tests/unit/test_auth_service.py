import time

import jwt
import pytest

from ygnt_web.core.config import get_settings
from ygnt_web.core.security.tokens import ACCES_DUREE_SECONDES
from ygnt_web.domain.exceptions import (
    IdentifiantsInvalides,
    JetonExpire,
    JetonInvalide,
    MotDePasseTropCourt,
)
from ygnt_web.services.auth_service import AuthService
from ygnt_web.services.role_service import RoleService
from ygnt_web.services.societe_service import SocieteService
from ygnt_web.services.utilisateur_service import UtilisateurService


def _creer_utilisateur_avec_mot_de_passe(
    connection, email="jean@acme.test", mot_de_passe="s3cret!!"
):
    societe = SocieteService(connection).creer_societe(nom="Acme")
    role = RoleService(connection).creer_role(societe_id=societe.id, nom="Producteur")
    utilisateur = UtilisateurService(connection).creer_utilisateur(
        societe_id=societe.id, nom="Dupont", prenom="Jean", email=email, role_id=role.id
    )
    AuthService(connection).definir_mot_de_passe(societe.id, utilisateur.id, mot_de_passe)
    return societe, role, utilisateur


def test_se_connecter_avec_de_bons_identifiants_renvoie_des_tokens(connection):
    _creer_utilisateur_avec_mot_de_passe(connection)
    service = AuthService(connection)

    tokens = service.se_connecter("jean@acme.test", "s3cret!!")

    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.expires_in == ACCES_DUREE_SECONDES


def test_se_connecter_avec_un_mauvais_mot_de_passe_echoue(connection):
    _creer_utilisateur_avec_mot_de_passe(connection)
    service = AuthService(connection)

    with pytest.raises(IdentifiantsInvalides):
        service.se_connecter("jean@acme.test", "mauvais-mot-de-passe")


def test_se_connecter_avec_un_email_inconnu_echoue(connection):
    service = AuthService(connection)

    with pytest.raises(IdentifiantsInvalides):
        service.se_connecter("inconnu@acme.test", "peu-importe")


def test_obtenir_contexte_renvoie_utilisateur_societe_et_roles(connection):
    societe, role, utilisateur = _creer_utilisateur_avec_mot_de_passe(connection)
    service = AuthService(connection)
    tokens = service.se_connecter("jean@acme.test", "s3cret!!")

    contexte = service.obtenir_contexte(tokens.access_token)

    assert contexte.utilisateur_id == utilisateur.id
    assert contexte.societe_id == societe.id
    assert contexte.roles == (role.nom,)


def test_obtenir_contexte_avec_un_jeton_expire_leve_une_erreur(connection):
    _, _, utilisateur = _creer_utilisateur_avec_mot_de_passe(connection)
    settings = get_settings()
    payload_expire = {
        "sub": str(utilisateur.id),
        "societe_id": 1,
        "roles": [],
        "iat": int(time.time()) - 1000,
        "exp": int(time.time()) - 1,
        "jti": "test",
        "type": "access",
    }
    jeton_expire = jwt.encode(payload_expire, settings.jwt_secret, algorithm="HS256")

    with pytest.raises(JetonExpire):
        AuthService(connection).obtenir_contexte(jeton_expire)


def test_obtenir_contexte_avec_un_jeton_invalide_leve_une_erreur(connection):
    with pytest.raises(JetonInvalide):
        AuthService(connection).obtenir_contexte("ceci-n-est-pas-un-jwt")


def test_rafraichir_emet_de_nouveaux_tokens_et_revoque_l_ancien(connection):
    _creer_utilisateur_avec_mot_de_passe(connection)
    service = AuthService(connection)
    tokens_initiaux = service.se_connecter("jean@acme.test", "s3cret!!")

    nouveaux_tokens = service.rafraichir(tokens_initiaux.refresh_token)

    assert nouveaux_tokens.refresh_token != tokens_initiaux.refresh_token
    with pytest.raises(JetonInvalide):
        service.rafraichir(tokens_initiaux.refresh_token)


def test_rafraichir_avec_un_jeton_inconnu_echoue(connection):
    service = AuthService(connection)

    with pytest.raises(JetonInvalide):
        service.rafraichir("jeton-qui-n-existe-pas")


def test_se_deconnecter_revoque_le_refresh_token(connection):
    _creer_utilisateur_avec_mot_de_passe(connection)
    service = AuthService(connection)
    tokens = service.se_connecter("jean@acme.test", "s3cret!!")

    service.se_deconnecter(tokens.refresh_token)

    with pytest.raises(JetonInvalide):
        service.rafraichir(tokens.refresh_token)


def test_definir_mot_de_passe_trop_court_echoue(connection):
    societe = SocieteService(connection).creer_societe(nom="Acme")
    role = RoleService(connection).creer_role(societe_id=societe.id, nom="Producteur")
    utilisateur = UtilisateurService(connection).creer_utilisateur(
        societe_id=societe.id,
        nom="Dupont",
        prenom="Jean",
        email="jean2@acme.test",
        role_id=role.id,
    )

    with pytest.raises(MotDePasseTropCourt):
        AuthService(connection).definir_mot_de_passe(societe.id, utilisateur.id, "short")
