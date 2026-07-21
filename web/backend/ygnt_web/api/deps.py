from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from ygnt_web.domain.auth_context import ContexteAuthentification
from ygnt_web.domain.exceptions import JetonExpire, JetonInvalide
from ygnt_web.services.auth_service import AuthService
from ygnt_web.storage.database import get_connection

_bearer_scheme = HTTPBearer(auto_error=False)


def obtenir_utilisateur_authentifie(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> ContexteAuthentification:
    """Middleware d'authentification : valide le jeton d'accès. N'a aucune
    connaissance métier au-delà de « qui est cet Utilisateur »."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentification requise."
        )

    with get_connection() as connection:
        try:
            return AuthService(connection).obtenir_contexte(credentials.credentials)
        except (JetonInvalide, JetonExpire):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Jeton invalide ou expiré."
            )


def obtenir_contexte_societe(
    contexte: ContexteAuthentification = Depends(obtenir_utilisateur_authentifie),
) -> ContexteAuthentification:
    """Middleware de contexte Société : la Société active n'est jamais un
    choix du Frontend, elle provient exclusivement du jeton déjà validé,
    signé par le serveur au moment de la connexion (06_ARCHITECTURE §4.4)."""
    return contexte


def exiger_role(*roles_autorises: str):
    """Contrôle des rôles : refuse l'accès si aucun rôle du jeton ne figure
    parmi ceux autorisés pour la route."""

    def dependency(
        contexte: ContexteAuthentification = Depends(obtenir_contexte_societe),
    ) -> ContexteAuthentification:
        if not set(contexte.roles) & set(roles_autorises):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Rôle insuffisant."
            )
        return contexte

    return dependency
