from dataclasses import dataclass
from typing import Optional


@dataclass
class PrestationParticipant:
    """Ligne de l'équipe de prestation - table de liaison many-to-many entre
    une Prestation et les Artistes qui y participent reellement (au-dela de
    la seule Formation vendue via le contrat de cession).

    Donnee strictement interne : jamais injectee automatiquement dans un
    contrat de cession, un devis ou une facture (voir
    docs/PRESTATIONS_ARCHITECTURE.md, section Équipe de prestation). Ne
    dupliqué aucune information de la fiche Artiste - seule la relation
    (qui participe, a quel rôle, dans quel ordre) est stockee ici."""

    id: Optional[int] = None

    prestation_id: Optional[int] = None
    artiste_id: Optional[int] = None

    role: str = ""
    ordre: Optional[int] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None
