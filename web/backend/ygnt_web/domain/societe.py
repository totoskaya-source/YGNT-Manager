from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class SocieteStatut(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass(frozen=True)
class Societe:
    id: int
    nom: str
    forme_juridique: str | None
    siret: str | None
    adresse: str | None
    code_postal: str | None
    ville: str | None
    email_contact: str | None
    statut: SocieteStatut
    date_creation: datetime
