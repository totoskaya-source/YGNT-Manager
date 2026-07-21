from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class UtilisateurStatut(str, Enum):
    INVITE = "invite"
    ACTIF = "actif"
    SUSPENDU = "suspendu"
    DESACTIVE = "desactive"


@dataclass(frozen=True)
class Utilisateur:
    id: int
    societe_id: int
    nom: str
    prenom: str
    email: str
    statut: UtilisateurStatut
    date_creation: datetime
