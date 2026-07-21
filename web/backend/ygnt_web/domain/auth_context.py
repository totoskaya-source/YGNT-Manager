from dataclasses import dataclass


@dataclass(frozen=True)
class ContexteAuthentification:
    """Le contexte courant (06_ARCHITECTURE.md §4.2) : établi une seule fois
    par le module Authentification, propagé tel quel aux couches suivantes,
    jamais redéfini ou reçu du Frontend."""

    utilisateur_id: int
    societe_id: int
    roles: tuple[str, ...]
