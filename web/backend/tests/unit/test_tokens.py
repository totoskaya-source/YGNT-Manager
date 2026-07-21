import jwt
import pytest

from ygnt_web.core.security.tokens import (
    ACCES_DUREE_SECONDES,
    decoder_access_token,
    generer_access_token,
    generer_refresh_token,
    hacher_refresh_token,
)


def test_generer_puis_decoder_un_access_token_renvoie_les_claims():
    token = generer_access_token(utilisateur_id=1, societe_id=2, roles=["Producteur"])

    payload = decoder_access_token(token)

    assert payload["sub"] == "1"
    assert payload["societe_id"] == 2
    assert payload["roles"] == ["Producteur"]
    assert payload["exp"] - payload["iat"] == ACCES_DUREE_SECONDES


def test_decoder_un_jeton_altere_echoue():
    token = generer_access_token(utilisateur_id=1, societe_id=2, roles=[])
    dernier_caractere = "A" if token[-1] != "A" else "B"
    jeton_altere = token[:-1] + dernier_caractere

    with pytest.raises(jwt.InvalidTokenError):
        decoder_access_token(jeton_altere)


def test_refresh_token_est_hache_de_maniere_deterministe_mais_non_reversible():
    token = generer_refresh_token()

    empreinte_1 = hacher_refresh_token(token)
    empreinte_2 = hacher_refresh_token(token)

    assert empreinte_1 == empreinte_2
    assert empreinte_1 != token
