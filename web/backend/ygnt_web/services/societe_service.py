from ygnt_web.domain.exceptions import NomSocieteObligatoire, SocieteInexistante
from ygnt_web.domain.societe import Societe
from ygnt_web.repositories.societe_repository import SocieteRepository
from ygnt_web.storage.connection import DatabaseConnection


class SocieteService:
    def __init__(self, connection: DatabaseConnection):
        self._societes = SocieteRepository(connection)

    def creer_societe(
        self,
        nom: str,
        forme_juridique: str | None = None,
        siret: str | None = None,
        adresse: str | None = None,
        code_postal: str | None = None,
        ville: str | None = None,
        email_contact: str | None = None,
    ) -> Societe:
        if not nom or not nom.strip():
            raise NomSocieteObligatoire()

        return self._societes.ajouter(
            nom=nom.strip(),
            forme_juridique=forme_juridique,
            siret=siret,
            adresse=adresse,
            code_postal=code_postal,
            ville=ville,
            email_contact=email_contact,
        )

    def obtenir_societe(self, societe_id: int) -> Societe:
        societe = self._societes.obtenir(societe_id)
        if societe is None:
            raise SocieteInexistante(societe_id)
        return societe
