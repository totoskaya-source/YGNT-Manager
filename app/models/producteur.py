from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Producteur:

    id: Optional[int] = None

    nom: str = ""
    forme_juridique: str = ""

    adresse: str = ""
    postal_code: str = ""
    city: str = ""

    siret: str = ""
    ape: str = ""
    licence: str = ""
    tva: str = ""

    iban: str = ""
    bic: str = ""

    representant: str = ""
    fonction: str = ""

    convention_collective: str = ""

    logo_path: str = ""
    site_internet: str = ""

    email: str = ""
    phone: str = ""

    notes: str = ""

    actif: bool = False

    created_at: Optional[str] = None
    updated_at: Optional[str] = None
