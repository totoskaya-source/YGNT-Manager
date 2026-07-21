from ygnt_web.services.auth_service import AuthService
from ygnt_web.services.role_service import RoleService
from ygnt_web.services.societe_service import SocieteService
from ygnt_web.services.utilisateur_service import UtilisateurService
from ygnt_web.storage.database import get_connection


def _creer_utilisateur_et_connecter(client, email, mot_de_passe="s3cret!!", nom_societe="Acme"):
    with get_connection() as connection:
        societe = SocieteService(connection).creer_societe(nom=nom_societe)
        role = RoleService(connection).creer_role(societe_id=societe.id, nom="Producteur")
        utilisateur = UtilisateurService(connection).creer_utilisateur(
            societe_id=societe.id, nom="Dupont", prenom="Jean", email=email, role_id=role.id
        )
        AuthService(connection).definir_mot_de_passe(societe.id, utilisateur.id, mot_de_passe)

    tokens = client.post("/auth/login", json={"email": email, "mot_de_passe": mot_de_passe}).json()
    return tokens["access_token"], societe


def _auth_headers(access_token):
    return {"Authorization": f"Bearer {access_token}"}


def test_creer_puis_obtenir_une_prestation(client):
    access_token, _ = _creer_utilisateur_et_connecter(client, "jean@acme.test")

    reponse_creation = client.post(
        "/prestations",
        json={"nom": "Concert de printemps", "date_debut": "2026-05-10"},
        headers=_auth_headers(access_token),
    )
    assert reponse_creation.status_code == 201
    corps = reponse_creation.json()
    assert corps["reference"] == "PREST-2026-0001"
    assert corps["statut"] == "prospection"
    assert corps["nom"] == "Concert de printemps"

    reponse_lecture = client.get(f"/prestations/{corps['id']}", headers=_auth_headers(access_token))
    assert reponse_lecture.status_code == 200
    assert reponse_lecture.json()["nom"] == "Concert de printemps"


def test_creer_prestation_sans_authentification_est_refuse(client):
    reponse = client.post("/prestations", json={"nom": "X", "date_debut": "2026-05-10"})
    assert reponse.status_code == 401


def test_creer_prestation_sans_nom_est_rejetee(client):
    access_token, _ = _creer_utilisateur_et_connecter(client, "jean2@acme.test")

    reponse = client.post(
        "/prestations", json={"nom": "  ", "date_debut": "2026-05-10"}, headers=_auth_headers(access_token)
    )
    assert reponse.status_code == 422


def test_creer_prestation_sans_date_debut_est_rejetee_par_le_schema(client):
    access_token, _ = _creer_utilisateur_et_connecter(client, "jean3@acme.test")

    reponse = client.post("/prestations", json={"nom": "Concert"}, headers=_auth_headers(access_token))
    assert reponse.status_code == 422


def test_modifier_une_prestation(client):
    access_token, _ = _creer_utilisateur_et_connecter(client, "jean4@acme.test")
    creation = client.post(
        "/prestations", json={"nom": "Concert", "date_debut": "2026-05-10"}, headers=_auth_headers(access_token)
    ).json()

    reponse = client.put(
        f"/prestations/{creation['id']}",
        json={"nom": "Concert modifié", "date_debut": "2026-05-11", "type_evenement": "festival"},
        headers=_auth_headers(access_token),
    )
    assert reponse.status_code == 200
    corps = reponse.json()
    assert corps["nom"] == "Concert modifié"
    assert corps["type_evenement"] == "festival"


def test_changer_le_statut_dune_prestation(client):
    access_token, _ = _creer_utilisateur_et_connecter(client, "jean5@acme.test")
    creation = client.post(
        "/prestations", json={"nom": "Concert", "date_debut": "2026-05-10"}, headers=_auth_headers(access_token)
    ).json()

    reponse = client.patch(
        f"/prestations/{creation['id']}/statut",
        json={"statut": "confirmee"},
        headers=_auth_headers(access_token),
    )
    assert reponse.status_code == 200
    assert reponse.json()["statut"] == "confirmee"


def test_dupliquer_une_prestation(client):
    access_token, _ = _creer_utilisateur_et_connecter(client, "jean6@acme.test")
    creation = client.post(
        "/prestations", json={"nom": "Concert", "date_debut": "2026-05-10"}, headers=_auth_headers(access_token)
    ).json()

    reponse = client.post(f"/prestations/{creation['id']}/dupliquer", headers=_auth_headers(access_token))
    assert reponse.status_code == 201
    copie = reponse.json()
    assert copie["id"] != creation["id"]
    assert copie["reference"] != creation["reference"]
    assert copie["statut"] == "prospection"
    assert copie["nom"] == "Concert (copie)"


def test_supprimer_une_prestation_est_une_suppression_logique(client):
    access_token, _ = _creer_utilisateur_et_connecter(client, "jean7@acme.test")
    creation = client.post(
        "/prestations", json={"nom": "Concert", "date_debut": "2026-05-10"}, headers=_auth_headers(access_token)
    ).json()

    reponse_suppression = client.delete(f"/prestations/{creation['id']}", headers=_auth_headers(access_token))
    assert reponse_suppression.status_code == 204

    reponse_lecture = client.get(f"/prestations/{creation['id']}", headers=_auth_headers(access_token))
    assert reponse_lecture.status_code == 404


def test_prestation_dune_societe_est_invisible_pour_une_autre(client):
    access_token_a, _ = _creer_utilisateur_et_connecter(client, "a@a.test", nom_societe="Société A")
    access_token_b, _ = _creer_utilisateur_et_connecter(client, "b@b.test", nom_societe="Société B")

    creation = client.post(
        "/prestations", json={"nom": "Concert A", "date_debut": "2026-05-10"}, headers=_auth_headers(access_token_a)
    ).json()

    reponse = client.get(f"/prestations/{creation['id']}", headers=_auth_headers(access_token_b))
    assert reponse.status_code == 404

    liste_b = client.get("/prestations", headers=_auth_headers(access_token_b)).json()
    assert liste_b["total"] == 0


def test_liste_paginee_recherche_et_tri(client):
    access_token, _ = _creer_utilisateur_et_connecter(client, "jean8@acme.test")
    for nom in ["Concert Jazz", "Mariage Dupont", "Festival Rock"]:
        client.post(
            "/prestations", json={"nom": nom, "date_debut": "2026-05-10"}, headers=_auth_headers(access_token)
        )

    reponse_page = client.get(
        "/prestations", params={"page": 1, "taille_page": 2}, headers=_auth_headers(access_token)
    )
    assert reponse_page.status_code == 200
    corps_page = reponse_page.json()
    assert corps_page["total"] == 3
    assert len(corps_page["items"]) == 2

    reponse_recherche = client.get(
        "/prestations", params={"recherche": "Jazz"}, headers=_auth_headers(access_token)
    )
    assert [p["nom"] for p in reponse_recherche.json()["items"]] == ["Concert Jazz"]

    reponse_tri = client.get(
        "/prestations", params={"tri": "nom", "ordre": "asc"}, headers=_auth_headers(access_token)
    )
    noms = [p["nom"] for p in reponse_tri.json()["items"]]
    assert noms == sorted(noms)
