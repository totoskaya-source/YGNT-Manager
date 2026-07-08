from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Organization:

    id: Optional[int] = None

    name: str = ""

    legal_form: str = ""

    address: str = ""
    postal_code: str = ""
    city: str = ""

    email: str = ""
    phone: str = ""

    siret: str = ""
    ape: str = ""
    licence: str = ""

    iban: str = ""
    bic: str = ""

    tva: str = ""
    president: str = ""
    fonction: str = ""
    site_internet: str = ""

    notes: str = ""

    created_at: Optional[str] = None
