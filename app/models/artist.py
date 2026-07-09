from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Artist:

    id: Optional[int] = None

    stage_name: str = ""
    legal_name: str = ""

    address: str = ""
    postal_code: str = ""
    city: str = ""

    email: str = ""
    phone: str = ""

    instrument: str = ""
    status: str = ""
    fee: float = 0.0

    birth_date: str = ""

    social_number: str = ""

    siren: str = ""
    siret: str = ""

    ape: str = ""
    licence: str = ""

    iban: str = ""
    bic: str = ""

    notes: str = ""

    # Champs marketing/informatifs (Sprint 8.7) : jamais imprimes automatiquement
    # dans un devis, un contrat ou une facture.
    style_musical: str = ""
    description: str = ""
    logo_path: str = ""
    photo_path: str = ""
    site_internet: str = ""
    facebook: str = ""
    instagram: str = ""
    youtube: str = ""

    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
