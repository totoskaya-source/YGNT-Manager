import hashlib
import hmac
import secrets

_ALGORITHME = "pbkdf2_sha256"
# Recommandation OWASP (2023) pour PBKDF2-HMAC-SHA256.
_ITERATIONS = 600_000


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    sel = secrets.token_hex(16)
    empreinte = hashlib.pbkdf2_hmac(
        "sha256", mot_de_passe.encode("utf-8"), sel.encode("utf-8"), _ITERATIONS
    )
    return f"{_ALGORITHME}${_ITERATIONS}${sel}${empreinte.hex()}"


def verifier_mot_de_passe(mot_de_passe: str, hash_stocke: str) -> bool:
    try:
        algorithme, iterations, sel, empreinte_attendue = hash_stocke.split("$")
    except ValueError:
        return False

    if algorithme != _ALGORITHME:
        return False

    empreinte = hashlib.pbkdf2_hmac(
        "sha256", mot_de_passe.encode("utf-8"), sel.encode("utf-8"), int(iterations)
    )
    return hmac.compare_digest(empreinte.hex(), empreinte_attendue)
