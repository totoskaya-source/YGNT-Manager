from ygnt_web.services.auth_service import AuthService
from ygnt_web.services.role_service import RoleService
from ygnt_web.services.societe_service import SocieteService
from ygnt_web.services.utilisateur_service import UtilisateurService
from ygnt_web.storage.database import get_connection


def _creer_utilisateur(email: str, mot_de_passe: str, nom_societe: str = "Acme"):
    with get_connection() as connection:
        societe = SocieteService(connection).creer_societe(nom=nom_societe)
        role = RoleService(connection).creer_role(societe_id=societe.id, nom="Producteur")
        utilisateur = UtilisateurService(connection).creer_utilisateur(
            societe_id=societe.id, nom="Dupont", prenom="Jean", email=email, role_id=role.id
        )
        AuthService(connection).definir_mot_de_passe(societe.id, utilisateur.id, mot_de_passe)
    return societe, role, utilisateur


def test_login_puis_me_renvoie_le_contexte_etabli_par_le_serveur(client):
    societe, role, utilisateur = _creer_utilisateur("jean@acme.test", "s3cret!!")

    reponse_login = client.post(
        "/auth/login", json={"email": "jean@acme.test", "mot_de_passe": "s3cret!!"}
    )
    assert reponse_login.status_code == 200
    tokens = reponse_login.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    reponse_me = client.get(
        "/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert reponse_me.status_code == 200
    corps = reponse_me.json()
    assert corps["utilisateur_id"] == utilisateur.id
    assert corps["societe_id"] == societe.id
    assert corps["roles"] == [role.nom]
    assert corps["utilisateur_nom"] == "Dupont"
    assert corps["utilisateur_prenom"] == "Jean"
    assert corps["societe_nom"] == societe.nom


def test_me_sans_jeton_est_refuse(client):
    reponse = client.get("/auth/me")

    assert reponse.status_code == 401


def test_me_avec_un_jeton_invalide_est_refuse(client):
    reponse = client.get("/auth/me", headers={"Authorization": "Bearer ceci-nest-pas-un-jwt"})

    assert reponse.status_code == 401


def test_login_avec_mauvais_mot_de_passe_est_refuse(client):
    _creer_utilisateur("jean2@acme.test", "s3cret!!")

    reponse = client.post(
        "/auth/login", json={"email": "jean2@acme.test", "mot_de_passe": "faux-mot-de-passe"}
    )

    assert reponse.status_code == 401


def test_refresh_puis_reutilisation_de_l_ancien_jeton_est_refusee(client):
    _creer_utilisateur("jean3@acme.test", "s3cret!!")
    tokens = client.post(
        "/auth/login", json={"email": "jean3@acme.test", "mot_de_passe": "s3cret!!"}
    ).json()

    reponse_refresh = client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert reponse_refresh.status_code == 200
    assert reponse_refresh.json()["refresh_token"] != tokens["refresh_token"]

    reponse_reutilisation = client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert reponse_reutilisation.status_code == 401


def test_logout_puis_refresh_est_refuse(client):
    _creer_utilisateur("jean4@acme.test", "s3cret!!")
    tokens = client.post(
        "/auth/login", json={"email": "jean4@acme.test", "mot_de_passe": "s3cret!!"}
    ).json()

    reponse_logout = client.post("/auth/logout", json={"refresh_token": tokens["refresh_token"]})
    assert reponse_logout.status_code == 204

    reponse_refresh = client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert reponse_refresh.status_code == 401
