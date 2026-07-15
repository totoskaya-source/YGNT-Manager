from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Artist:

    id: Optional[int] = None

    stage_name: str = ""
    legal_name: str = ""
    first_name: str = ""

    address: str = ""
    postal_code: str = ""
    city: str = ""

    email: str = ""
    phone: str = ""

    instrument: str = ""
    secondary_instruments: str = ""
    status: str = ""
    # Qualification juridique (Sprint 18.2) : categorie professionnelle
    # utilisee par le CDDU pour la mention "en qualite de {{qualification}}"
    # - jamais codee en dur, toujours issue de cette fiche. Distincte de
    # `instrument` (specialite technique) : "Danseur"/"Technicien du
    # spectacle" n'ont pas d'instrument, "Artiste musicien" en a un.
    qualification: str = ""
    fee: float = 0.0

    birth_date: str = ""
    birth_place: str = ""

    social_number: str = ""
    conges_spectacle_number: str = ""

    siren: str = ""
    siret: str = ""

    ape: str = ""
    licence: str = ""

    iban: str = ""
    bic: str = ""

    notes: str = ""
    comments: str = ""

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
    
