import hashlib
import secrets
import time
import uuid

import jwt

from ygnt_web.core.config import get_settings

ALGORITHME_JWT = "HS256"
ACCES_DUREE_SECONDES = 15 * 60
RAFRAICHISSEMENT_DUREE_SECONDES = 30 * 24 * 60 * 60


def generer_access_token(utilisateur_id: int, societe_id: int, roles: list[str]) -> str:
    """Le contenu (dont societe_id) est entièrement déterminé côté serveur au
    moment de l'appel : le Frontend ne fournit jamais cette valeur."""
    settings = get_settings()
    maintenant = int(time.time())
    payload = {
        "sub": str(utilisateur_id),
        "societe_id": societe_id,
        "roles": roles,
        "iat": maintenant,
        "exp": maintenant + ACCES_DUREE_SECONDES,
        "jti": str(uuid.uuid4()),
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHME_JWT)


def decoder_access_token(token: str) -> dict:
    """Lève jwt.ExpiredSignatureError ou jwt.InvalidTokenError si le jeton
    n'est pas valide — laissé à la charge de l'appelant (couche Services)."""
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHME_JWT])
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Type de jeton inattendu.")
    return payload


def generer_refresh_token() -> str:
    """Jeton opaque (jamais un JWT) : seule sa forme hachée est persistée,
    pour qu'une fuite de la base de données ne permette pas de le rejouer."""
    return secrets.token_urlsafe(48)


def hacher_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
