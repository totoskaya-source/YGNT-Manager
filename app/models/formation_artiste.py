from dataclasses import dataclass
from typing import Optional


@dataclass
class FormationArtiste:
    """Une ligne = un membre de la composition d'une Formation - table de
    liaison many-to-many entre Formation et Artiste. Donnee interne a la
    Formation ; ne dupliqué aucune information de la fiche Artiste (seule la
    relation - qui, quel rôle, quel ordre - est stockee ici), meme principe
    que PrestationParticipant (docs/PRESTATIONS_ARCHITECTURE.md)."""

    id: Optional[int] = None

    formation_id: Optional[int] = None
    artiste_id: Optional[int] = None

    role: str = ""
    ordre: Optional[int] = None

    created_at: Optional[str] = None
    updated_at: Optional[str] = None
