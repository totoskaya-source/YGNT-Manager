from dataclasses import dataclass
from typing import Optional


@dataclass
class Paiement:

    id: Optional[int] = None

    reference: str = ""

    facture_id: Optional[int] = None

    date_paiement: str = ""

    montant: float = 0.0

    mode_paiement: str = ""
    reference_bancaire: str = ""
    observations: str = ""

    status: str = "pending"

    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    def to_dict(self):
        values = {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
        }

        values.update({
            "status_label": self.status_label,
        })
        return values

    @property
    def status_label(self) -> str:
        labels = {
            "pending": "En attente",
            "partial": "Partiel",
            "paid": "Payé",
            "cancelled": "Annulé",
        }
        return labels.get(self.status, self.status)
