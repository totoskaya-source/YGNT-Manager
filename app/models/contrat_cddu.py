from dataclasses import dataclass
from typing import Optional


@dataclass
class ContratCddu:

    id: Optional[int] = None

    numero: str = ""

    prestation_id: Optional[int] = None
    artist_id: Optional[int] = None
    producteur_id: Optional[int] = None

    producteur_nom: str = ""
    producteur_forme_juridique: str = ""
    producteur_adresse: str = ""
    producteur_postal_code: str = ""
    producteur_city: str = ""
    producteur_siret: str = ""
    producteur_ape: str = ""
    producteur_licence: str = ""
    producteur_convention_collective: str = ""
    producteur_representant: str = ""
    producteur_fonction: str = ""
    producteur_email: str = ""
    producteur_phone: str = ""

    artiste_nom: str = ""
    # Prenom du salarie (Sprint 18.2) : le contrat doit toujours afficher le
    # nom complet (prenom + nom), jamais le seul nom de famille.
    artiste_prenom: str = ""
    artiste_adresse: str = ""
    artiste_postal_code: str = ""
    artiste_city: str = ""
    artiste_phone: str = ""
    artiste_email: str = ""
    artiste_date_naissance: str = ""
    artiste_lieu_naissance: str = ""
    artiste_numero_secu: str = ""
    artiste_numero_conges_spectacle: str = ""
    artiste_fonction: str = ""
    # Categorie professionnelle (Sprint 18.2) : instantane de
    # artists.qualification au moment de la creation, utilisee pour la
    # mention "en qualite de ..." - jamais de valeur codee en dur.
    artiste_qualification: str = ""

    prestation_reference: str = ""
    prestation_objet: str = ""
    prestation_lieu: str = ""
    prestation_ville: str = ""

    # Reserve pour un usage metier futur (voir docs/CDDU_ARCHITECTURE.md, §9) :
    # toujours vide, aucune logique de calcul ou de generation a ce stade.
    numero_objet: str = ""

    remuneration_brute: float = 0.0

    defraiement_deplacement: float = 0.0
    defraiement_hebergement: float = 0.0
    defraiement_repas: float = 0.0
    defraiement_autres_libelle: str = ""
    defraiement_autres_montant: float = 0.0
    defraiement_montant_libre_libelle: str = ""
    defraiement_montant_libre_montant: float = 0.0

    observations: str = ""

    ville_signature: str = ""
    date_signature: str = ""

    docx_path: str = ""
    pdf_path: str = ""

    status: str = "draft"

    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    generated_at: Optional[str] = None

    def to_dict(self) -> dict:
        values = {
            field: getattr(self, field)
            for field in self.__dataclass_fields__
        }
        values.update({
            "status_label": self.status_label,
            "producteur_adresse_complete": self.producteur_adresse_complete,
            "artiste_adresse_complete": self.artiste_adresse_complete,
            "prestation_lieu_complet": self.prestation_lieu_complet,
            "artiste_nom_complet": self.artiste_nom_complet,
        })
        return values

    @property
    def status_label(self) -> str:
        labels = {
            "draft": "Brouillon",
            "validated": "Validé",
            "pdf_generated": "PDF généré",
            "sent": "Envoyé",
            "signed": "Signé",
            "archived": "Archivé",
        }
        return labels.get(self.status, self.status)

    @property
    def producteur_adresse_complete(self) -> str:
        """Adresse complete de l'employeur, sans virgule ni espace parasite
        si une partie est manquante (meme principe que
        Contract.prestation_lieu_complet)."""
        code_ville = " ".join(part for part in (self.producteur_postal_code, self.producteur_city) if part)
        parts = (self.producteur_adresse, code_ville)
        return ", ".join(part for part in parts if part)

    @property
    def artiste_adresse_complete(self) -> str:
        """Adresse complete du salarié, meme principe que
        producteur_adresse_complete."""
        code_ville = " ".join(part for part in (self.artiste_postal_code, self.artiste_city) if part)
        parts = (self.artiste_adresse, code_ville)
        return ", ".join(part for part in parts if part)

    @property
    def prestation_lieu_complet(self) -> str:
        """Lieu du projet (nom + ville), meme principe que
        Contract.prestation_lieu_complet."""
        parts = (self.prestation_lieu, self.prestation_ville)
        return ", ".join(part for part in parts if part)

    @property
    def artiste_nom_complet(self) -> str:
        """Nom complet du salarié - "Prénom NOM" (nom de famille en
        majuscules), convention standard des contrats. Le contrat n'affiche
        jamais le seul nom de famille (Sprint 18.2). Si l'un des deux
        manque, affiche simplement ce qui est disponible plutot que de
        fabriquer une majuscule trompeuse sur un fragment isole."""
        prenom = (self.artiste_prenom or "").strip()
        nom = (self.artiste_nom or "").strip()
        if prenom and nom:
            return f"{prenom} {nom.upper()}"
        return prenom or nom
