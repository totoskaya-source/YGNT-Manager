from dataclasses import dataclass

import jwt

from ygnt_web.core.security.passwords import hacher_mot_de_passe, verifier_mot_de_passe
from ygnt_web.core.security.tokens import (
    ACCES_DUREE_SECONDES,
    RAFRAICHISSEMENT_DUREE_SECONDES,
    decoder_access_token,
    generer_access_token,
    generer_refresh_token,
    hacher_refresh_token,
)
from ygnt_web.domain.auth_context import ContexteAuthentification
from ygnt_web.domain.exceptions import (
    IdentifiantsInvalides,
    JetonExpire,
    JetonInvalide,
    MotDePasseTropCourt,
    UtilisateurInexistant,
)
from ygnt_web.repositories.identifiant_repository import IdentifiantRepository
from ygnt_web.repositories.refresh_token_repository import RefreshTokenRepository
from ygnt_web.repositories.role_repository import RoleRepository
from ygnt_web.repositories.utilisateur_repository import UtilisateurRepository
from ygnt_web.storage.connection import DatabaseConnection

_LONGUEUR_MINIMALE_MOT_DE_PASSE = 8


@dataclass(frozen=True)
class TokensAuthentification:
    access_token: str
    refresh_token: str
    expires_in: int


class AuthService:
    def __init__(self, connection: DatabaseConnection):
        self._utilisateurs = UtilisateurRepository(connection)
        self._roles = RoleRepository(connection)
        self._identifiants = IdentifiantRepository(connection)
        self._refresh_tokens = RefreshTokenRepository(connection)

    def definir_mot_de_passe(
        self, societe_id: int, utilisateur_id: int, mot_de_passe: str
    ) -> None:
        """`societe_id` est le tenant du contexte authentifié de l'appelant.
        Le Repository refuse l'écriture (T4) si `utilisateur_id` n'appartient
        pas à cette Société ; ce cas est alors traité comme un Utilisateur
        introuvable, pas comme une erreur distincte."""
        if len(mot_de_passe) < _LONGUEUR_MINIMALE_MOT_DE_PASSE:
            raise MotDePasseTropCourt(_LONGUEUR_MINIMALE_MOT_DE_PASSE)
        reussi = self._identifiants.definir_mot_de_passe(
            societe_id, utilisateur_id, hacher_mot_de_passe(mot_de_passe)
        )
        if not reussi:
            raise UtilisateurInexistant(utilisateur_id)

    def se_connecter(self, email: str, mot_de_passe: str) -> TokensAuthentification:
        utilisateur = self._utilisateurs.obtenir_par_email(email)
        if utilisateur is None:
            raise IdentifiantsInvalides()

        hash_stocke = self._identifiants.obtenir_hash(utilisateur.id)
        if hash_stocke is None or not verifier_mot_de_passe(mot_de_passe, hash_stocke):
            raise IdentifiantsInvalides()

        return self._emettre_tokens(utilisateur.id, utilisateur.societe_id)

    def rafraichir(self, refresh_token: str) -> TokensAuthentification:
        token_hash = hacher_refresh_token(refresh_token)
        enregistrement = self._refresh_tokens.obtenir_valide(token_hash)
        if enregistrement is None:
            raise JetonInvalide()

        # Rotation : un jeton de rafraîchissement ne sert jamais deux fois.
        self._refresh_tokens.revoquer(token_hash)

        # societe_id vient de l'enregistrement du jeton (dénormalisé à
        # l'émission), jamais d'une relecture non filtrée par Société de
        # utilisateurs (T4) : aucun appel à UtilisateurRepository ici.
        return self._emettre_tokens(enregistrement.utilisateur_id, enregistrement.societe_id)

    def se_deconnecter(self, refresh_token: str) -> None:
        self._refresh_tokens.revoquer(hacher_refresh_token(refresh_token))

    def obtenir_contexte(self, access_token: str) -> ContexteAuthentification:
        try:
            payload = decoder_access_token(access_token)
        except jwt.ExpiredSignatureError:
            raise JetonExpire()
        except jwt.InvalidTokenError:
            raise JetonInvalide()

        return ContexteAuthentification(
            utilisateur_id=int(payload["sub"]),
            societe_id=payload["societe_id"],
            roles=tuple(payload.get("roles", [])),
        )

    def _emettre_tokens(self, utilisateur_id: int, societe_id: int) -> TokensAuthentification:
        roles = [
            role.nom for role in self._roles.lister_roles_utilisateur(societe_id, utilisateur_id)
        ]

        access_token = generer_access_token(utilisateur_id, societe_id, roles)
        refresh_token = generer_refresh_token()
        self._refresh_tokens.creer(
            utilisateur_id,
            societe_id,
            hacher_refresh_token(refresh_token),
            RAFRAICHISSEMENT_DUREE_SECONDES,
        )

        return TokensAuthentification(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=ACCES_DUREE_SECONDES,
        )
