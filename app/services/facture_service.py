from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from app.contracts.pdf_converter import PdfConverter
from app.database.database import PROJECT_ROOT
from app.factures.generator import FactureGenerator
from app.models.contract import Contract
from app.models.facture import Facture
from app.models.prestation import Prestation
from app.paths import resource_path
from app.repositories.facture_repository import FactureRepository
from app.services.artist_service import ArtistService
from app.services.formation_service import FormationService
from app.services.producteur_service import ProducteurService


class FactureService:
    # Le statut d'une facture reflete son etat de reglement, determine
    # automatiquement par PaiementService a partir de compute_facture_status()
    # apres chaque creation/modification/suppression d'un paiement. Seul
    # 'cancelled' reste modifiable manuellement (annulation administrative,
    # independante du suivi des paiements).
    STATUSES = {
        "pending": "En attente",
        "partial": "Partiel",
        "paid": "Payée",
        "cancelled": "Annulée",
    }

    def __init__(
        self,
        repository: FactureRepository | None = None,
        producteur_service: ProducteurService | None = None,
        formation_service: FormationService | None = None,
        artist_service: ArtistService | None = None,
    ) -> None:
        self.repository = repository or FactureRepository()
        self.producteur_service = producteur_service or ProducteurService()
        self.formation_service = formation_service or FormationService()
        self.artist_service = artist_service or ArtistService()
        self.template_path = resource_path("templates", "facture.docx")
        self.exports_dir = PROJECT_ROOT / "exports"

    def list_factures(self) -> list[Facture]:
        return self.repository.get_all()

    def list_for_prestation(self, prestation_id: int) -> list[Facture]:
        """Factures rattachees a une prestation (Dossier), via prestation_id
        uniquement : aucune duplication de donnee, simple requete croisee."""
        return [facture for facture in self.list_factures() if facture.prestation_id == prestation_id]

    def list_for_contract(self, contract_id: int) -> list[Facture]:
        """Factures rattachees a un contrat, via contract_id uniquement :
        aucune duplication de donnee, simple requete croisee."""
        return [facture for facture in self.list_factures() if facture.contract_id == contract_id]

    def build_from_prestation(self, prestation: Prestation) -> Facture:
        """Prepare une facture pre-remplie (formation, organisateur, date, lieu)
        a partir d'une prestation. La facture n'est pas enregistrée : c'est un
        point de depart, toujours modifiable avant validation (meme philosophie
        que ContractService.build_from_prestation).

        Sprint 20 : priorite a prestation.formation_id (vraie entite
        Formation). Si la prestation est ancienne et ne porte que artist_id,
        comportement historique preserve a l'identique - compatibilite
        totale, aucune prestation existante ne perd son pre-remplissage."""
        facture = Facture(
            prestation_id=prestation.id,
            formation_id=prestation.formation_id if prestation.formation_id is not None else prestation.artist_id,
            organization_id=prestation.organization_id,
            spectacle_nom=prestation.nom,
            prestation_date=prestation.date_debut,
            prestation_lieu=prestation.lieu_nom,
            prestation_adresse=prestation.lieu_adresse,
            prestation_postal_code=prestation.lieu_postal_code,
            prestation_city=prestation.lieu_city,
            comments=prestation.notes,
        )

        if prestation.formation_id is not None:
            self._apply_formation_snapshot(facture, prestation.formation_id)
        elif prestation.artist_id is not None:
            self._apply_artist_snapshot(facture, prestation.artist_id)

        return facture

    def _apply_formation_snapshot(self, facture: Facture, formation_id: int) -> None:
        """Copie les informations de la vraie Formation dans l'instantane
        formation_* de la facture (meme principe que
        ContractService._apply_formation_snapshot)."""
        formation = self.formation_service.get_formation(formation_id)
        if formation is None:
            return

        facture.formation_nom = formation.nom
        facture.formation_adresse = formation.address
        facture.formation_postal_code = formation.postal_code
        facture.formation_city = formation.city
        facture.formation_phone = formation.phone
        facture.formation_email = formation.email
        facture.formation_siret = formation.siret
        facture.formation_ape = formation.ape
        facture.formation_licence = formation.licence
        facture.formation_iban = formation.iban
        facture.formation_bic = formation.bic
        facture.formation_notes = formation.description

    def _apply_artist_snapshot(self, facture: Facture, artist_id: int) -> None:
        """Comportement historique (avant l'entite Formation) : une
        prestation ancienne ne porte que artist_id, l'instantane formation_*
        de la facture est alors repris de la fiche Artiste - inchange."""
        artist = self.artist_service.get_artist(artist_id)
        if artist is None:
            return

        facture.formation_nom = artist.stage_name or artist.legal_name
        facture.formation_adresse = artist.address
        facture.formation_postal_code = artist.postal_code
        facture.formation_city = artist.city
        facture.formation_phone = artist.phone
        facture.formation_email = artist.email
        facture.formation_site_internet = artist.site_internet
        facture.formation_siren = artist.siren
        facture.formation_siret = artist.siret
        facture.formation_ape = artist.ape
        facture.formation_licence = artist.licence
        facture.formation_iban = artist.iban
        facture.formation_bic = artist.bic
        facture.formation_social_number = artist.social_number
        facture.formation_notes = artist.notes

    def build_from_contract(self, contract: Contract) -> Facture:
        """Prepare une facture pre-remplie (formation, organisateur, objet,
        date, lieu, conditions financières) a partir d'un Contrat honore. La
        facture n'est pas enregistrée : c'est un nouveau document independant,
        toujours modifiable avant validation. Le Contrat n'est jamais modifié
        (meme philosophie que ContractService.build_from_devis).

        Le Producteur n'est volontairement pas copie depuis le Contrat : comme
        pour toute nouvelle facture, FactureService.create_facture() lui
        appliquera l'instantane du Producteur actif au moment de la creation.

        Sprint 20 : priorite a contract.formation_id (sinon contract.artist_id
        pour compatibilite), et l'instantane formation_* de la facture est
        repris directement de l'instantane artiste_* deja fige sur le
        Contrat (jamais recalcule depuis la Formation/l'Artiste d'origine -
        le Contrat, une fois cree, est la source de verite, meme s'il a ete
        modifie manuellement depuis)."""
        facture = Facture(
            prestation_id=contract.prestation_id,
            contract_id=contract.id,
            formation_id=contract.formation_id if contract.formation_id is not None else contract.artist_id,
            organization_id=contract.organization_id,
            spectacle_nom=contract.spectacle_nom,
            spectacle_duree=contract.spectacle_duree,
            prestation_date=contract.prestation_date,
            prestation_lieu=contract.prestation_lieu,
            prestation_adresse=contract.prestation_adresse,
            prestation_postal_code=contract.prestation_postal_code,
            prestation_city=contract.prestation_city,
            comments=contract.comments,
            montant=contract.cession_montant,
            tva=contract.cachet_tva,
            acompte=contract.acompte,
            mode_paiement=contract.mode_paiement,
            echeance=contract.echeance,
            formation_nom=contract.artiste_nom,
            formation_adresse=contract.artiste_adresse,
            formation_postal_code=contract.artiste_postal_code,
            formation_city=contract.artiste_city,
            formation_phone=contract.artiste_phone,
            formation_email=contract.artiste_email,
            formation_siret=contract.artiste_siret,
            formation_ape=contract.artiste_ape,
            formation_licence=contract.artiste_licence,
            formation_iban=contract.artiste_iban,
            formation_bic=contract.artiste_bic,
        )
        return facture

    def search_factures(self, query: str = "", status: str = "all") -> list[Facture]:
        normalized_query = query.strip().casefold()
        items = self.list_factures()

        if status != "all":
            items = [facture for facture in items if facture.status == status]

        if not normalized_query:
            return items

        return [
            facture
            for facture in items
            if normalized_query in self._search_text(facture)
        ]

    def get_facture(self, facture_id: int) -> Facture | None:
        return self.repository.get_by_id(facture_id)

    def create_facture(self, facture: Facture) -> int:
        self._prepare(facture)
        facture.facture_number = facture.facture_number or self.next_facture_number()
        self._apply_producteur_snapshot(facture)
        return self.repository.insert(facture)

    def update_facture(self, facture: Facture) -> None:
        if facture.id is None:
            raise ValueError("Impossible de modifier une facture sans identifiant.")

        self._prepare(facture)
        self.repository.update(facture)

    def delete_facture(self, facture_id: int) -> None:
        self.repository.delete(facture_id)

    def update_status(self, facture_id: int, status: str) -> None:
        """Met a jour UNIQUEMENT le statut d'une facture : aucun autre champ
        (montant inclus) n'est touche. Utilise par PaiementService pour
        refleter automatiquement l'etat de reglement après chaque
        creation/modification/suppression d'un paiement."""
        self.repository.update_status(facture_id, status)

    def next_facture_number(self) -> str:
        year = datetime.now().year
        sequence = self.repository.next_sequence(year)
        return f"FACT-{year}-{sequence:04d}"

    def generate_docx(self, facture_id: int) -> Path:
        facture = self._require(facture_id)
        self._prepare(facture)
        output = self._docx_output_path(facture)
        output.parent.mkdir(exist_ok=True)

        generator = FactureGenerator(self.template_path)
        generator.generate(facture, str(output))

        self.repository.mark_generated(facture_id, str(output))
        return output

    def generate_pdf(self, facture_id: int) -> Path:
        docx_path = self.generate_docx(facture_id)

        facture = self._require(facture_id)
        output = self._pdf_output_path(facture)
        output.parent.mkdir(exist_ok=True)

        PdfConverter().convert(docx_path, output)

        self.repository.mark_pdf_exported(facture_id, str(output))
        return output

    def open_document(self, facture_id: int) -> Path:
        facture = self._require(facture_id)
        path = Path(facture.docx_path or "")

        if not path.exists():
            raise FileNotFoundError("Aucun document DOCX généré pour cette facture.")

        self._open_path(path)
        return path

    def open_pdf(self, facture_id: int) -> Path:
        facture = self._require(facture_id)
        path = Path(facture.pdf_path or "")

        if not path.exists():
            raise FileNotFoundError("Aucun PDF généré pour cette facture.")

        self._open_path(path)
        return path

    def preview(self, facture: Facture) -> str:
        self._prepare(facture)
        lines = [
            f"Référence : {facture.facture_number or '(automatique)'}",
            f"Producteur : {facture.producteur_nom or '-'}",
            f"Formation : {facture.formation_nom or '-'}",
            f"Organisateur : {facture.organisateur_structure or '-'}",
            f"Objet : {facture.spectacle_nom or '-'}",
            f"Date : {facture.prestation_date or '-'}",
            f"Lieu : {facture.prestation_lieu_complet or '-'}",
            f"Montant : {float(facture.montant or 0):.2f} EUR",
            f"TVA : {facture.tva or '-'}",
            f"Acompte : {float(facture.acompte or 0):.2f} EUR",
            f"Total : {float(facture.total or 0):.2f} EUR",
            f"Mode de paiement : {facture.mode_paiement or '-'}",
            f"Échéance : {facture.echeance or '-'}",
            f"Statut : {self.STATUSES.get(facture.status, facture.status)}",
        ]

        if facture.observations:
            lines.extend(["", "Observations", str(facture.observations)])
        if facture.comments:
            lines.extend(["", "Notes", str(facture.comments)])

        return "\n".join(lines)

    def _prepare(self, facture: Facture) -> None:
        facture.producteur_nom = str(facture.producteur_nom or "").strip()
        facture.producteur_forme_juridique = str(facture.producteur_forme_juridique or "").strip()
        facture.producteur_adresse = str(facture.producteur_adresse or "").strip()
        facture.producteur_code_postal = str(facture.producteur_code_postal or "").strip()
        facture.producteur_ville = str(facture.producteur_ville or "").strip()
        facture.producteur_siret = str(facture.producteur_siret or "").strip()
        facture.producteur_ape = str(facture.producteur_ape or "").strip()
        facture.producteur_licence = str(facture.producteur_licence or "").strip()
        facture.producteur_tva_intracommunautaire = str(facture.producteur_tva_intracommunautaire or "").strip()
        facture.producteur_telephone = str(facture.producteur_telephone or "").strip()
        facture.producteur_email = str(facture.producteur_email or "").strip()
        facture.producteur_site = str(facture.producteur_site or "").strip()
        facture.producteur_representant = str(facture.producteur_representant or "").strip()
        facture.producteur_fonction = str(facture.producteur_fonction or "").strip()
        facture.producteur_iban = str(facture.producteur_iban or "").strip()
        facture.producteur_bic = str(facture.producteur_bic or "").strip()
        facture.producteur_logo_path = str(facture.producteur_logo_path or "").strip()

        facture.organisateur_structure = str(facture.organisateur_structure or "").strip()
        facture.organisateur_forme = str(facture.organisateur_forme or "").strip()
        facture.organisateur_adresse = str(facture.organisateur_adresse or "").strip()
        facture.organisateur_postal_code = str(facture.organisateur_postal_code or "").strip()
        facture.organisateur_city = str(facture.organisateur_city or "").strip()
        facture.organisateur_siret = str(facture.organisateur_siret or "").strip()
        facture.organisateur_phone = str(facture.organisateur_phone or "").strip()
        facture.organisateur_email = str(facture.organisateur_email or "").strip()
        facture.organisateur_ape = str(facture.organisateur_ape or "").strip()
        facture.organisateur_licence = str(facture.organisateur_licence or "").strip()
        facture.organisateur_tva = str(facture.organisateur_tva or "").strip()
        facture.organisateur_representant = str(facture.organisateur_representant or "").strip()
        facture.organisateur_fonction = str(facture.organisateur_fonction or "").strip()
        facture.organisateur_iban = str(facture.organisateur_iban or "").strip()
        facture.organisateur_bic = str(facture.organisateur_bic or "").strip()
        facture.organisateur_site_internet = str(facture.organisateur_site_internet or "").strip()
        facture.organisateur_notes = str(facture.organisateur_notes or "").strip()

        facture.formation_nom = str(facture.formation_nom or "").strip()
        facture.formation_adresse = str(facture.formation_adresse or "").strip()
        facture.formation_postal_code = str(facture.formation_postal_code or "").strip()
        facture.formation_city = str(facture.formation_city or "").strip()
        facture.formation_phone = str(facture.formation_phone or "").strip()
        facture.formation_email = str(facture.formation_email or "").strip()
        facture.formation_site_internet = str(facture.formation_site_internet or "").strip()
        facture.formation_siren = str(facture.formation_siren or "").strip()
        facture.formation_siret = str(facture.formation_siret or "").strip()
        facture.formation_ape = str(facture.formation_ape or "").strip()
        facture.formation_licence = str(facture.formation_licence or "").strip()
        facture.formation_iban = str(facture.formation_iban or "").strip()
        facture.formation_bic = str(facture.formation_bic or "").strip()
        facture.formation_social_number = str(facture.formation_social_number or "").strip()
        facture.formation_notes = str(facture.formation_notes or "").strip()

        facture.spectacle_nom = str(facture.spectacle_nom or "").strip()
        facture.spectacle_duree = str(facture.spectacle_duree or "").strip()

        facture.prestation_date = str(facture.prestation_date or "").strip()
        facture.prestation_lieu = str(facture.prestation_lieu or "").strip()
        facture.prestation_adresse = str(facture.prestation_adresse or "").strip()
        facture.prestation_postal_code = str(facture.prestation_postal_code or "").strip()
        facture.prestation_city = str(facture.prestation_city or "").strip()
        facture.prestation_convocation = str(facture.prestation_convocation or "").strip()
        facture.prestation_horaire = str(facture.prestation_horaire or "").strip()

        facture.tva = str(facture.tva or "").strip()
        facture.mode_paiement = str(facture.mode_paiement or "").strip()
        facture.echeance = str(facture.echeance or "").strip()
        facture.observations = str(facture.observations or "").strip()
        facture.comments = str(facture.comments or "").strip()
        facture.status = facture.status or "pending"

        if not facture.organisateur_structure:
            raise ValueError("L'organisateur est obligatoire.")
        if not facture.spectacle_nom:
            raise ValueError("Le spectacle est obligatoire.")

        try:
            facture.montant = float(facture.montant or 0)
        except (TypeError, ValueError):
            facture.montant = 0.0

        try:
            facture.acompte = float(facture.acompte or 0)
        except (TypeError, ValueError):
            facture.acompte = 0.0

        # Total = reste du apres deduction de l'acompte deja verse.
        facture.total = round(facture.montant - facture.acompte, 2)

    def _apply_producteur_snapshot(self, facture: Facture) -> None:
        """Copie l'instantane du Producteur actif sur une NOUVELLE facture. Ne
        doit jamais être appele lors d'une modification : la facture existante
        conserve les informations figees a sa creation, meme si la fiche
        Producteur change ensuite (meme principe que l'instantane des Contrats
        et des Devis)."""
        if facture.producteur_id is not None:
            return

        producteur = self.producteur_service.get_active_producteur()
        if producteur is None:
            return

        facture.producteur_id = producteur.id
        facture.producteur_nom = producteur.nom
        facture.producteur_forme_juridique = producteur.forme_juridique
        facture.producteur_adresse = producteur.adresse
        facture.producteur_code_postal = producteur.postal_code
        facture.producteur_ville = producteur.city
        facture.producteur_siret = producteur.siret
        facture.producteur_ape = producteur.ape
        facture.producteur_licence = producteur.licence
        facture.producteur_tva_intracommunautaire = producteur.tva
        facture.producteur_telephone = producteur.phone
        facture.producteur_email = producteur.email
        facture.producteur_site = producteur.site_internet
        facture.producteur_representant = producteur.representant
        facture.producteur_fonction = producteur.fonction
        facture.producteur_iban = producteur.iban
        facture.producteur_bic = producteur.bic
        facture.producteur_logo_path = producteur.logo_path

    def _require(self, facture_id: int) -> Facture:
        facture = self.get_facture(facture_id)
        if facture is None:
            raise ValueError("Facture introuvable.")
        return facture

    def _search_text(self, facture: Facture) -> str:
        values = (
            facture.facture_number,
            facture.organisateur_structure,
            facture.organisateur_forme,
            facture.organisateur_adresse,
            facture.organisateur_city,
            facture.organisateur_siret,
            facture.formation_nom,
            facture.spectacle_nom,
            facture.prestation_date,
            facture.prestation_adresse,
            facture.status_label,
        )
        return " ".join(str(value or "") for value in values).casefold()

    def _docx_output_path(self, facture: Facture) -> Path:
        filename = (
            f"{facture.facture_number or self.next_facture_number()} - "
            f"{facture.prestation_date.replace('/', '-')} - "
            f"{facture.organisateur_structure} - "
            f"{facture.spectacle_nom}.docx"
        )
        return self.exports_dir / self._safe_filename(filename)

    def _pdf_output_path(self, facture: Facture) -> Path:
        stem = self._docx_output_path(facture).stem
        return self.exports_dir / f"{stem}.pdf"

    def _safe_filename(self, filename: str) -> str:
        return re.sub(r'[<>:"/\\\\|?*]', "-", filename).strip()

    def _open_path(self, path: Path) -> None:
        import os

        os.startfile(path)
