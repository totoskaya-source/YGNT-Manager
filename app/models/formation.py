from dataclasses import dataclass
from typing import Optional


@dataclass
class Formation:
    """Une Formation represente un groupe (l'entite artistique vendue dans un
    contrat de cession) - jamais une personne. Sa composition (qui en fait
    partie) vit exclusivement dans la table de liaison formation_artistes,
    chaque membre etant une fiche Artiste existante (voir
    docs/PRESTATIONS_ARCHITECTURE.md, Sprint 18.0)."""

    id: Optional[int] = None

    nom: str = ""

    logo_path: str = ""
    photo_path: str = ""
    description: str = ""
    style: str = ""

    # Coordonnees et informations legales (Sprint 18.1) : necessaires pour que
    # le contrat de cession puisse s'appuyer entierement sur la Formation
    # (nom, adresse, SIRET...) sans jamais avoir besoin d'une fiche Artiste.
    # Aucun champ personnel (SIREN, numero de securite sociale) : une
    # Formation n'est jamais une personne.
    address: str = ""
    postal_code: str = ""
    city: str = ""
    phone: str = ""
    email: str = ""
    siret: str = ""
    ape: str = ""
    licence: str = ""
    iban: str = ""
    bic: str = ""

    created_at: Optional[str] = None
    updated_at: Optional[str] = None
