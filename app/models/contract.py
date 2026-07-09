from dataclasses import dataclass
from typing import Optional


@dataclass
class Contract:

    id: Optional[int] = None

    contract_number: str = ""

    artist_id: Optional[int] = None
    organization_id: Optional[int] = None
    prestation_id: Optional[int] = None
    producteur_id: Optional[int] = None

    event_name: str = ""
    venue: str = ""

    event_date: str = ""

    start_time: str = ""
    end_time: str = ""

    gross_salary: float = 0.0
    employer_cost: float = 0.0

    travel_cost: float = 0.0
    accommodation_cost: float = 0.0
    catering_cost: float = 0.0

    comments: str = ""

    docx_path: str = ""
    pdf_path: str = ""

    status: str = "draft"

    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    generated_at: Optional[str] = None

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

    artiste_nom: str = ""
    artiste_adresse: str = ""
    artiste_postal_code: str = ""
    artiste_city: str = ""
    artiste_phone: str = ""
    artiste_email: str = ""
    artiste_siren: str = ""
    artiste_siret: str = ""
    artiste_ape: str = ""
    artiste_licence: str = ""
    artiste_iban: str = ""
    artiste_bic: str = ""
    artiste_social_number: str = ""
    artiste_notes: str = ""

    spectacle_nom: str = ""
    spectacle_duree: str = ""

    prestation_date: str = ""
    prestation_lieu: str = ""
    prestation_adresse: str = ""
    prestation_postal_code: str = ""
    prestation_city: str = ""
    prestation_convocation: str = ""
    prestation_horaire: str = ""

    cession_montant: float | str = 0.0
    acompte: float = 0.0
    cachet_tva: str = ""
    echeance: str = ""
    observations: str = ""
    mode_paiement: str = ""
    hebergement: bool = False
    restauration: bool = False
    kilometrage: bool = False

    def to_dict(self):
        values = {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
        }

        values.update({
            "event_name": self.event_name or self.spectacle_nom,
            "venue": self.venue or self.prestation_lieu or self.prestation_adresse,
            "event_date": self.event_date or self.prestation_date,
            "gross_salary": self.gross_salary or self.cession_montant,
            "status_label": self.status_label,
            "prestation_lieu_complet": self.prestation_lieu_complet,
        })
        return values

    @property
    def status_label(self) -> str:
        labels = {
            "draft": "Brouillon",
            "validated": "Valide",
            "signed": "Signe",
        }
        return labels.get(self.status, self.status)

    @property
    def prestation_lieu_complet(self) -> str:
        """Adresse complete du lieu de la prestation (distincte du siege de l'organisateur)."""
        code_ville = " ".join(part for part in (self.prestation_postal_code, self.prestation_city) if part)
        parts = (self.prestation_lieu, self.prestation_adresse, code_ville)
        return ", ".join(part for part in parts if part)

