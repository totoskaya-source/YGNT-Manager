from dataclasses import dataclass
from typing import Optional


@dataclass
class Devis:

    id: Optional[int] = None

    devis_number: str = ""

    formation_id: Optional[int] = None
    organization_id: Optional[int] = None
    prestation_id: Optional[int] = None
    producteur_id: Optional[int] = None

    producteur_nom: str = ""
    producteur_forme_juridique: str = ""
    producteur_adresse: str = ""
    producteur_code_postal: str = ""
    producteur_ville: str = ""
    producteur_siret: str = ""
    producteur_ape: str = ""
    producteur_licence: str = ""
    producteur_tva_intracommunautaire: str = ""
    producteur_telephone: str = ""
    producteur_email: str = ""
    producteur_site: str = ""
    producteur_representant: str = ""
    producteur_fonction: str = ""
    producteur_iban: str = ""
    producteur_bic: str = ""
    producteur_logo_path: str = ""

    organisateur_structure: str = ""
    organisateur_forme: str = ""
    organisateur_adresse: str = ""
    organisateur_postal_code: str = ""
    organisateur_city: str = ""
    organisateur_siret: str = ""
    organisateur_phone: str = ""
    organisateur_email: str = ""
    organisateur_ape: str = ""
    organisateur_licence: str = ""
    organisateur_tva: str = ""
    organisateur_representant: str = ""
    organisateur_fonction: str = ""
    organisateur_iban: str = ""
    organisateur_bic: str = ""
    organisateur_site_internet: str = ""
    organisateur_notes: str = ""

    formation_nom: str = ""
    formation_adresse: str = ""
    formation_postal_code: str = ""
    formation_city: str = ""
    formation_phone: str = ""
    formation_email: str = ""
    formation_site_internet: str = ""
    formation_siren: str = ""
    formation_siret: str = ""
    formation_ape: str = ""
    formation_licence: str = ""
    formation_iban: str = ""
    formation_bic: str = ""
    formation_social_number: str = ""
    formation_notes: str = ""

    spectacle_nom: str = ""
    spectacle_duree: str = ""

    prestation_date: str = ""
    prestation_lieu: str = ""
    prestation_adresse: str = ""
    prestation_postal_code: str = ""
    prestation_city: str = ""
    prestation_convocation: str = ""
    prestation_horaire: str = ""

    montant: float = 0.0
    acompte: float = 0.0
    tva: str = ""
    mode_paiement: str = ""
    echeance: str = ""
    date_validite: str = ""
    observations: str = ""
    comments: str = ""

    hebergement: bool = False
    restauration: bool = False
    kilometrage: bool = False

    docx_path: str = ""
    pdf_path: str = ""

    status: str = "draft"

    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    generated_at: Optional[str] = None

    def to_dict(self):
        values = {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
        }

        values.update({
            "status_label": self.status_label,
            "prestation_lieu_complet": self.prestation_lieu_complet,
        })
        return values

    @property
    def status_label(self) -> str:
        labels = {
            "draft": "Brouillon",
            "sent": "Envoye",
            "accepted": "Accepte",
            "refused": "Refuse",
            "expired": "Expire",
        }
        return labels.get(self.status, self.status)

    @property
    def prestation_lieu_complet(self) -> str:
        """Adresse complete du lieu de la prestation (distincte du siege de l'organisateur)."""
        code_ville = " ".join(part for part in (self.prestation_postal_code, self.prestation_city) if part)
        parts = (self.prestation_lieu, self.prestation_adresse, code_ville)
        return ", ".join(part for part in parts if part)
