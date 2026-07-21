from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ygnt_web.api.deps import obtenir_contexte_societe
from ygnt_web.domain.auth_context import ContexteAuthentification
from ygnt_web.domain.exceptions import IdentifiantsInvalides, JetonInvalide
from ygnt_web.services.auth_service import AuthService, TokensAuthentification
from ygnt_web.services.societe_service import SocieteService
from ygnt_web.services.utilisateur_service import UtilisateurService
from ygnt_web.storage.database import get_connection

router = APIRouter(prefix="/auth", tags=["auth"])


class ConnexionRequete(BaseModel):
    email: str
    mot_de_passe: str


class RafraichissementRequete(BaseModel):
    refresh_token: str


class TokensReponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

    @classmethod
    def depuis(cls, tokens: TokensAuthentification) -> "TokensReponse":
        return cls(
            access_token=tokens.access_token,
            refresh_token=tokens.refresh_token,
            expires_in=tokens.expires_in,
        )


@router.post("/login", response_model=TokensReponse)
def login(requete: ConnexionRequete) -> TokensReponse:
    with get_connection() as connection:
        try:
            tokens = AuthService(connection).se_connecter(requete.email, requete.mot_de_passe)
        except IdentifiantsInvalides:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Email ou mot de passe incorrect."
            )
    return TokensReponse.depuis(tokens)


@router.post("/refresh", response_model=TokensReponse)
def refresh(requete: RafraichissementRequete) -> TokensReponse:
    with get_connection() as connection:
        try:
            tokens = AuthService(connection).rafraichir(requete.refresh_token)
        except JetonInvalide:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Jeton de rafraîchissement invalide ou expiré.",
            )
    return TokensReponse.depuis(tokens)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(requete: RafraichissementRequete) -> None:
    with get_connection() as connection:
        AuthService(connection).se_deconnecter(requete.refresh_token)


@router.get("/me")
def me(contexte: ContexteAuthentification = Depends(obtenir_contexte_societe)) -> dict:
    """Enrichit le contexte (déjà validé par le jeton) avec des libellés
    lisibles — nom de l'Utilisateur, nom de la Société — nécessaires à leur
    affichage (T5). `roles` reste issu du jeton (§3.4/§5 06_ARCHITECTURE) ;
    les champs d'affichage sont relus en base pour rester à jour, même si
    l'Utilisateur ou la Société ont été renommés depuis la connexion."""
    with get_connection() as connection:
        utilisateur = UtilisateurService(connection).obtenir_utilisateur(
            contexte.societe_id, contexte.utilisateur_id
        )
        societe = SocieteService(connection).obtenir_societe(contexte.societe_id)

    return {
        "utilisateur_id": contexte.utilisateur_id,
        "societe_id": contexte.societe_id,
        "roles": list(contexte.roles),
        "utilisateur_nom": utilisateur.nom,
        "utilisateur_prenom": utilisateur.prenom,
        "societe_nom": societe.nom,
    }
