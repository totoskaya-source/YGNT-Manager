from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from ygnt_web.api.deps import obtenir_contexte_societe
from ygnt_web.domain.auth_context import ContexteAuthentification
from ygnt_web.domain.exceptions import (
    DateDebutObligatoire,
    NomPrestationObligatoire,
    PrestationInexistante,
)
from ygnt_web.domain.prestation import Prestation, PrestationStatut, TypeEvenement
from ygnt_web.repositories.prestation_repository import PagePrestations
from ygnt_web.services.prestation_service import PrestationService
from ygnt_web.storage.database import get_connection

router = APIRouter(prefix="/prestations", tags=["prestations"])


class PrestationRequete(BaseModel):
    nom: str = Field(min_length=1)
    date_debut: date
    type_evenement: TypeEvenement = TypeEvenement.AUTRE
    date_fin: Optional[date] = None
    lieu_nom: Optional[str] = None
    lieu_adresse: Optional[str] = None
    lieu_code_postal: Optional[str] = None
    lieu_ville: Optional[str] = None
    notes: Optional[str] = None


class StatutRequete(BaseModel):
    statut: PrestationStatut


class PrestationReponse(BaseModel):
    id: int
    reference: str
    type_evenement: TypeEvenement
    nom: str
    statut: PrestationStatut
    date_debut: date
    date_fin: Optional[date]
    lieu_nom: Optional[str]
    lieu_adresse: Optional[str]
    lieu_code_postal: Optional[str]
    lieu_ville: Optional[str]
    notes: Optional[str]

    @classmethod
    def depuis(cls, prestation: Prestation) -> "PrestationReponse":
        return cls(
            id=prestation.id,
            reference=prestation.reference,
            type_evenement=prestation.type_evenement,
            nom=prestation.nom,
            statut=prestation.statut,
            date_debut=date.fromisoformat(prestation.date_debut),
            date_fin=date.fromisoformat(prestation.date_fin) if prestation.date_fin else None,
            lieu_nom=prestation.lieu_nom,
            lieu_adresse=prestation.lieu_adresse,
            lieu_code_postal=prestation.lieu_code_postal,
            lieu_ville=prestation.lieu_ville,
            notes=prestation.notes,
        )


class PagePrestationsReponse(BaseModel):
    items: list[PrestationReponse]
    total: int
    page: int
    taille_page: int

    @classmethod
    def depuis(cls, page_resultat: PagePrestations) -> "PagePrestationsReponse":
        return cls(
            items=[PrestationReponse.depuis(p) for p in page_resultat.items],
            total=page_resultat.total,
            page=page_resultat.page,
            taille_page=page_resultat.taille_page,
        )


def _erreur_validation(erreur: Exception) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(erreur))


def _erreur_introuvable() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Prestation introuvable.")


@router.post("", response_model=PrestationReponse, status_code=status.HTTP_201_CREATED)
def creer_prestation(
    requete: PrestationRequete,
    contexte: ContexteAuthentification = Depends(obtenir_contexte_societe),
) -> PrestationReponse:
    with get_connection() as connection:
        try:
            prestation = PrestationService(connection).creer_prestation(
                societe_id=contexte.societe_id,
                nom=requete.nom,
                date_debut=requete.date_debut.isoformat(),
                type_evenement=requete.type_evenement,
                date_fin=requete.date_fin.isoformat() if requete.date_fin else None,
                lieu_nom=requete.lieu_nom,
                lieu_adresse=requete.lieu_adresse,
                lieu_code_postal=requete.lieu_code_postal,
                lieu_ville=requete.lieu_ville,
                notes=requete.notes,
            )
        except (NomPrestationObligatoire, DateDebutObligatoire) as erreur:
            raise _erreur_validation(erreur)
    return PrestationReponse.depuis(prestation)


@router.get("", response_model=PagePrestationsReponse)
def lister_prestations(
    contexte: ContexteAuthentification = Depends(obtenir_contexte_societe),
    page: int = Query(1, ge=1),
    taille_page: int = Query(20, ge=1, le=100),
    recherche: Optional[str] = Query(None),
    statut: Optional[PrestationStatut] = Query(None),
    type_evenement: Optional[TypeEvenement] = Query(None),
    tri: str = Query("date_debut"),
    ordre: str = Query("desc"),
) -> PagePrestationsReponse:
    with get_connection() as connection:
        resultat = PrestationService(connection).lister_prestations(
            societe_id=contexte.societe_id,
            page=page,
            taille_page=taille_page,
            recherche=recherche,
            statut=statut,
            type_evenement=type_evenement,
            tri=tri,
            ordre=ordre,
        )
    return PagePrestationsReponse.depuis(resultat)


@router.get("/{prestation_id}", response_model=PrestationReponse)
def obtenir_prestation(
    prestation_id: int,
    contexte: ContexteAuthentification = Depends(obtenir_contexte_societe),
) -> PrestationReponse:
    with get_connection() as connection:
        try:
            prestation = PrestationService(connection).obtenir_prestation(
                contexte.societe_id, prestation_id
            )
        except PrestationInexistante:
            raise _erreur_introuvable()
    return PrestationReponse.depuis(prestation)


@router.put("/{prestation_id}", response_model=PrestationReponse)
def modifier_prestation(
    prestation_id: int,
    requete: PrestationRequete,
    contexte: ContexteAuthentification = Depends(obtenir_contexte_societe),
) -> PrestationReponse:
    with get_connection() as connection:
        try:
            prestation = PrestationService(connection).modifier_prestation(
                contexte.societe_id,
                prestation_id,
                nom=requete.nom,
                date_debut=requete.date_debut.isoformat(),
                type_evenement=requete.type_evenement,
                date_fin=requete.date_fin.isoformat() if requete.date_fin else None,
                lieu_nom=requete.lieu_nom,
                lieu_adresse=requete.lieu_adresse,
                lieu_code_postal=requete.lieu_code_postal,
                lieu_ville=requete.lieu_ville,
                notes=requete.notes,
            )
        except PrestationInexistante:
            raise _erreur_introuvable()
        except (NomPrestationObligatoire, DateDebutObligatoire) as erreur:
            raise _erreur_validation(erreur)
    return PrestationReponse.depuis(prestation)


@router.patch("/{prestation_id}/statut", response_model=PrestationReponse)
def changer_statut_prestation(
    prestation_id: int,
    requete: StatutRequete,
    contexte: ContexteAuthentification = Depends(obtenir_contexte_societe),
) -> PrestationReponse:
    with get_connection() as connection:
        try:
            prestation = PrestationService(connection).changer_statut(
                contexte.societe_id, prestation_id, requete.statut
            )
        except PrestationInexistante:
            raise _erreur_introuvable()
    return PrestationReponse.depuis(prestation)


@router.post("/{prestation_id}/dupliquer", response_model=PrestationReponse, status_code=status.HTTP_201_CREATED)
def dupliquer_prestation(
    prestation_id: int,
    contexte: ContexteAuthentification = Depends(obtenir_contexte_societe),
) -> PrestationReponse:
    with get_connection() as connection:
        try:
            prestation = PrestationService(connection).dupliquer_prestation(
                contexte.societe_id, prestation_id
            )
        except PrestationInexistante:
            raise _erreur_introuvable()
    return PrestationReponse.depuis(prestation)


@router.delete("/{prestation_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_prestation(
    prestation_id: int,
    contexte: ContexteAuthentification = Depends(obtenir_contexte_societe),
) -> None:
    with get_connection() as connection:
        try:
            PrestationService(connection).supprimer_prestation(contexte.societe_id, prestation_id)
        except PrestationInexistante:
            raise _erreur_introuvable()
