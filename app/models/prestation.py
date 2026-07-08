from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class Prestation:

    id: Optional[int] = None

    reference: str = ""

    type_evenement: str = ""
    nom: str = ""

    statut: str = "prospection"

    date_debut: str = ""
    date_fin: str = ""

    artist_id: Optional[int] = None
    organization_id: Optional[int] = None

    lieu_nom: str = ""
    lieu_adresse: str = ""
    lieu_postal_code: str = ""
    lieu_city: str = ""

    notes: str = ""

    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @property
    def statut_label(self) -> str:
        labels = {
            "prospection": "Prospection",
            "devis_envoye": "Devis envoye",
            "confirmee": "Confirmee",
            "realisee": "Realisee",
            "facturee": "Facturee",
            "soldee": "Soldee",
            "archivee": "Archivee",
            "annulee": "Annulee",
        }
        return labels.get(self.statut, self.statut)
