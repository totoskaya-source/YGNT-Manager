from ygnt_web.domain.exceptions import DateDebutObligatoire, NomPrestationObligatoire, PrestationInexistante
from ygnt_web.domain.prestation import Prestation, PrestationStatut, TypeEvenement
from ygnt_web.repositories.prestation_repository import PagePrestations, PrestationRepository
from ygnt_web.storage.connection import DatabaseConnection


class PrestationService:
    def __init__(self, connection: DatabaseConnection):
        self._prestations = PrestationRepository(connection)

    def creer_prestation(
        self,
        societe_id: int,
        nom: str,
        date_debut: str,
        type_evenement: TypeEvenement = TypeEvenement.AUTRE,
        date_fin: str | None = None,
        lieu_nom: str | None = None,
        lieu_adresse: str | None = None,
        lieu_code_postal: str | None = None,
        lieu_ville: str | None = None,
        notes: str | None = None,
    ) -> Prestation:
        """Organisateur et Formation ne sont pas obligatoires à la création
        (02_DOMAIN_MODEL §3.8) — ils n'existent d'ailleurs pas encore comme
        modules à ce stade, voir storage/migrations.py. Le statut initial
        est toujours Prospection, jamais un choix de l'appelant."""
        self._valider(nom, date_debut)

        annee = date_debut[:4]
        sequence = self._prestations.prochaine_sequence(societe_id, annee)
        reference = f"PREST-{annee}-{sequence:04d}"

        return self._prestations.ajouter(
            societe_id=societe_id,
            reference=reference,
            type_evenement=type_evenement,
            nom=nom.strip(),
            statut=PrestationStatut.PROSPECTION,
            date_debut=date_debut,
            date_fin=date_fin,
            lieu_nom=lieu_nom,
            lieu_adresse=lieu_adresse,
            lieu_code_postal=lieu_code_postal,
            lieu_ville=lieu_ville,
            notes=notes,
        )

    def obtenir_prestation(self, societe_id: int, prestation_id: int) -> Prestation:
        prestation = self._prestations.obtenir(societe_id, prestation_id)
        if prestation is None:
            raise PrestationInexistante(prestation_id)
        return prestation

    def modifier_prestation(
        self,
        societe_id: int,
        prestation_id: int,
        nom: str,
        date_debut: str,
        type_evenement: TypeEvenement,
        date_fin: str | None = None,
        lieu_nom: str | None = None,
        lieu_adresse: str | None = None,
        lieu_code_postal: str | None = None,
        lieu_ville: str | None = None,
        notes: str | None = None,
    ) -> Prestation:
        """Remplacement complet des champs modifiables (sémantique PUT) : la
        référence, le statut et la Société ne se modifient jamais par cette
        voie."""
        self._valider(nom, date_debut)

        prestation = self._prestations.modifier(
            societe_id,
            prestation_id,
            nom=nom.strip(),
            date_debut=date_debut,
            date_fin=date_fin,
            type_evenement=type_evenement,
            lieu_nom=lieu_nom,
            lieu_adresse=lieu_adresse,
            lieu_code_postal=lieu_code_postal,
            lieu_ville=lieu_ville,
            notes=notes,
        )
        if prestation is None:
            raise PrestationInexistante(prestation_id)
        return prestation

    def changer_statut(
        self, societe_id: int, prestation_id: int, statut: PrestationStatut
    ) -> Prestation:
        prestation = self._prestations.modifier(societe_id, prestation_id, statut=statut)
        if prestation is None:
            raise PrestationInexistante(prestation_id)
        return prestation

    def supprimer_prestation(self, societe_id: int, prestation_id: int) -> None:
        if not self._prestations.supprimer(societe_id, prestation_id):
            raise PrestationInexistante(prestation_id)

    def dupliquer_prestation(self, societe_id: int, prestation_id: int) -> Prestation:
        """Repart d'un modèle (même principe que la duplication de Contrat
        côté Desktop) : nouvelle référence, statut réinitialisé à
        Prospection via creer_prestation — jamais une copie du statut ou de
        la référence d'origine."""
        source = self.obtenir_prestation(societe_id, prestation_id)
        return self.creer_prestation(
            societe_id=societe_id,
            nom=f"{source.nom} (copie)",
            date_debut=source.date_debut,
            type_evenement=source.type_evenement,
            date_fin=source.date_fin,
            lieu_nom=source.lieu_nom,
            lieu_adresse=source.lieu_adresse,
            lieu_code_postal=source.lieu_code_postal,
            lieu_ville=source.lieu_ville,
            notes=source.notes,
        )

    def lister_prestations(
        self,
        societe_id: int,
        page: int = 1,
        taille_page: int = 20,
        recherche: str | None = None,
        statut: PrestationStatut | None = None,
        type_evenement: TypeEvenement | None = None,
        tri: str = "date_debut",
        ordre: str = "desc",
    ) -> PagePrestations:
        return self._prestations.lister(
            societe_id,
            page=page,
            taille_page=taille_page,
            recherche=recherche,
            statut=statut,
            type_evenement=type_evenement,
            tri=tri,
            ordre=ordre,
        )

    @staticmethod
    def _valider(nom: str, date_debut: str) -> None:
        if not nom or not str(nom).strip():
            raise NomPrestationObligatoire()
        if not date_debut:
            raise DateDebutObligatoire()
