from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TypeEvenement(str, Enum):
    MARIAGE = "mariage"
    FESTIVAL = "festival"
    MAIRIE = "mairie"
    COMITE_ENTREPRISE = "comite_entreprise"
    ANNIVERSAIRE = "anniversaire"
    SOIREE_PRIVEE = "soiree_privee"
    AUTRE = "autre"


class PrestationStatut(str, Enum):
    """Cycle de vie repris de 02_DOMAIN_MODEL.md §3.8 / §6.2. Les transitions
    exactement autorisées entre statuts restent une décision ouverte
    (§9 point 14) : ce module n'impose donc aucune restriction de
    transition, tous les statuts sont atteignables depuis n'importe quel
    autre via changer_statut()."""

    PROSPECTION = "prospection"
    DEVIS_ENVOYE = "devis_envoye"
    CONFIRMEE = "confirmee"
    REALISEE = "realisee"
    FACTUREE = "facturee"
    SOLDEE = "soldee"
    ARCHIVEE = "archivee"
    ANNULEE = "annulee"


@dataclass(frozen=True)
class Prestation:
    id: int
    societe_id: int
    reference: str
    type_evenement: TypeEvenement
    nom: str
    statut: PrestationStatut
    date_debut: str
    date_fin: str | None
    lieu_nom: str | None
    lieu_adresse: str | None
    lieu_code_postal: str | None
    lieu_ville: str | None
    notes: str | None
    date_creation: datetime
    supprime_le: datetime | None
