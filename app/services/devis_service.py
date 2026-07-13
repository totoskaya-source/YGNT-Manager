from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from app.contracts.pdf_converter import PdfConverter
from app.database.database import PROJECT_ROOT
from app.devis.generator import DevisGenerator
from app.models.devis import Devis
from app.models.prestation import Prestation
from app.paths import resource_path
from app.repositories.devis_repository import DevisRepository
from app.services.producteur_service import ProducteurService


class DevisService:
    STATUSES = {
        "draft": "Brouillon",
        "sent": "Envoye",
        "accepted": "Accepte",
        "refused": "Refuse",
        "expired": "Expire",
    }

    def __init__(
        self,
        repository: DevisRepository | None = None,
        producteur_service: ProducteurService | None = None,
    ) -> None:
        self.repository = repository or DevisRepository()
        self.producteur_service = producteur_service or ProducteurService()
        self.template_path = resource_path("templates", "devis.docx")
        self.exports_dir = PROJECT_ROOT / "exports"

    def list_devis(self) -> list[Devis]:
        return self.repository.get_all()

    def list_for_prestation(self, prestation_id: int) -> list[Devis]:
        """Devis rattaches a une prestation (Dossier), via prestation_id
        uniquement : aucune duplication de donnee, simple requete croisee."""
        return [devis for devis in self.list_devis() if devis.prestation_id == prestation_id]

    def build_from_prestation(self, prestation: Prestation) -> Devis:
        """Prepare un devis pre-rempli (formation, organisateur, date, lieu,
        objet, description) a partir d'une prestation. Le devis n'est pas
        enregistre : c'est un point de depart, toujours modifiable avant
        validation (meme philosophie que ContractService.build_from_prestation)."""
        return Devis(
            prestation_id=prestation.id,
            formation_id=prestation.artist_id,
            organization_id=prestation.organization_id,
            spectacle_nom=prestation.nom,
            prestation_date=prestation.date_debut,
            prestation_lieu=prestation.lieu_nom,
            prestation_adresse=prestation.lieu_adresse,
            prestation_postal_code=prestation.lieu_postal_code,
            prestation_city=prestation.lieu_city,
            comments=prestation.notes,
        )

    def search_devis(self, query: str = "", status: str = "all") -> list[Devis]:
        normalized_query = query.strip().casefold()
        items = self.list_devis()

        if status != "all":
            items = [devis for devis in items if devis.status == status]

        if not normalized_query:
            return items

        return [
            devis
            for devis in items
            if normalized_query in self._search_text(devis)
        ]

    def get_devis(self, devis_id: int) -> Devis | None:
        return self.repository.get_by_id(devis_id)

    def create_devis(self, devis: Devis) -> int:
        self._prepare(devis)
        devis.devis_number = devis.devis_number or self.next_devis_number()
        self._apply_producteur_snapshot(devis)
        return self.repository.insert(devis)

    def update_devis(self, devis: Devis) -> None:
        if devis.id is None:
            raise ValueError("Impossible de modifier un devis sans identifiant.")

        self._prepare(devis)
        self.repository.update(devis)

    def delete_devis(self, devis_id: int) -> None:
        self.repository.delete(devis_id)

    def next_devis_number(self) -> str:
        year = datetime.now().year
        sequence = self.repository.next_sequence(year)
        return f"DEVIS-{year}-{sequence:04d}"

    def generate_docx(self, devis_id: int) -> Path:
        devis = self._require(devis_id)
        self._prepare(devis)
        output = self._docx_output_path(devis)
        output.parent.mkdir(exist_ok=True)

        generator = DevisGenerator(self.template_path)
        generator.generate(devis, str(output))

        self.repository.mark_generated(devis_id, str(output))
        return output

    def generate_pdf(self, devis_id: int) -> Path:
        docx_path = self.generate_docx(devis_id)

        devis = self._require(devis_id)
        output = self._pdf_output_path(devis)
        output.parent.mkdir(exist_ok=True)

        PdfConverter().convert(docx_path, output)

        self.repository.mark_pdf_exported(devis_id, str(output))
        return output

    def open_document(self, devis_id: int) -> Path:
        devis = self._require(devis_id)
        path = Path(devis.docx_path or "")

        if not path.exists():
            raise FileNotFoundError("Aucun document DOCX genere pour ce devis.")

        self._open_path(path)
        return path

    def open_pdf(self, devis_id: int) -> Path:
        devis = self._require(devis_id)
        path = Path(devis.pdf_path or "")

        if not path.exists():
            raise FileNotFoundError("Aucun PDF genere pour ce devis.")

        self._open_path(path)
        return path

    def preview(self, devis: Devis) -> str:
        self._prepare(devis)
        lines = [
            f"Reference : {devis.devis_number or '(automatique)'}",
            f"Producteur : {devis.producteur_nom or '-'}",
            f"Formation : {devis.formation_nom or '-'}",
            f"Organisateur : {devis.organisateur_structure or '-'}",
            f"Objet : {devis.spectacle_nom or '-'}",
            f"Date : {devis.prestation_date or '-'}",
            f"Lieu : {devis.prestation_lieu_complet or '-'}",
            f"Duree : {devis.spectacle_duree or '-'}",
            f"Date de validite : {devis.date_validite or '-'}",
            f"Montant : {float(devis.montant or 0):.2f} EUR",
            f"Acompte : {float(devis.acompte or 0):.2f} EUR",
            f"TVA : {devis.tva or '-'}",
            f"Mode de paiement : {devis.mode_paiement or '-'}",
            f"Echeance : {devis.echeance or '-'}",
            f"Statut : {self.STATUSES.get(devis.status, devis.status)}",
        ]

        if devis.observations:
            lines.extend(["", "Observations", str(devis.observations)])
        if devis.comments:
            lines.extend(["", "Notes", str(devis.comments)])

        return "\n".join(lines)

    def _prepare(self, devis: Devis) -> None:
        devis.producteur_nom = str(devis.producteur_nom or "").strip()
        devis.producteur_forme_juridique = str(devis.producteur_forme_juridique or "").strip()
        devis.producteur_adresse = str(devis.producteur_adresse or "").strip()
        devis.producteur_code_postal = str(devis.producteur_code_postal or "").strip()
        devis.producteur_ville = str(devis.producteur_ville or "").strip()
        devis.producteur_siret = str(devis.producteur_siret or "").strip()
        devis.producteur_ape = str(devis.producteur_ape or "").strip()
        devis.producteur_licence = str(devis.producteur_licence or "").strip()
        devis.producteur_tva_intracommunautaire = str(devis.producteur_tva_intracommunautaire or "").strip()
        devis.producteur_telephone = str(devis.producteur_telephone or "").strip()
        devis.producteur_email = str(devis.producteur_email or "").strip()
        devis.producteur_site = str(devis.producteur_site or "").strip()
        devis.producteur_representant = str(devis.producteur_representant or "").strip()
        devis.producteur_fonction = str(devis.producteur_fonction or "").strip()
        devis.producteur_iban = str(devis.producteur_iban or "").strip()
        devis.producteur_bic = str(devis.producteur_bic or "").strip()
        devis.producteur_logo_path = str(devis.producteur_logo_path or "").strip()

        devis.organisateur_structure = str(devis.organisateur_structure or "").strip()
        devis.organisateur_forme = str(devis.organisateur_forme or "").strip()
        devis.organisateur_adresse = str(devis.organisateur_adresse or "").strip()
        devis.organisateur_postal_code = str(devis.organisateur_postal_code or "").strip()
        devis.organisateur_city = str(devis.organisateur_city or "").strip()
        devis.organisateur_siret = str(devis.organisateur_siret or "").strip()
        devis.organisateur_phone = str(devis.organisateur_phone or "").strip()
        devis.organisateur_email = str(devis.organisateur_email or "").strip()
        devis.organisateur_ape = str(devis.organisateur_ape or "").strip()
        devis.organisateur_licence = str(devis.organisateur_licence or "").strip()
        devis.organisateur_tva = str(devis.organisateur_tva or "").strip()
        devis.organisateur_representant = str(devis.organisateur_representant or "").strip()
        devis.organisateur_fonction = str(devis.organisateur_fonction or "").strip()
        devis.organisateur_iban = str(devis.organisateur_iban or "").strip()
        devis.organisateur_bic = str(devis.organisateur_bic or "").strip()
        devis.organisateur_site_internet = str(devis.organisateur_site_internet or "").strip()
        devis.organisateur_notes = str(devis.organisateur_notes or "").strip()

        devis.formation_nom = str(devis.formation_nom or "").strip()
        devis.formation_adresse = str(devis.formation_adresse or "").strip()
        devis.formation_postal_code = str(devis.formation_postal_code or "").strip()
        devis.formation_city = str(devis.formation_city or "").strip()
        devis.formation_phone = str(devis.formation_phone or "").strip()
        devis.formation_email = str(devis.formation_email or "").strip()
        devis.formation_site_internet = str(devis.formation_site_internet or "").strip()
        devis.formation_siren = str(devis.formation_siren or "").strip()
        devis.formation_siret = str(devis.formation_siret or "").strip()
        devis.formation_ape = str(devis.formation_ape or "").strip()
        devis.formation_licence = str(devis.formation_licence or "").strip()
        devis.formation_iban = str(devis.formation_iban or "").strip()
        devis.formation_bic = str(devis.formation_bic or "").strip()
        devis.formation_social_number = str(devis.formation_social_number or "").strip()
        devis.formation_notes = str(devis.formation_notes or "").strip()

        devis.spectacle_nom = str(devis.spectacle_nom or "").strip()
        devis.spectacle_duree = str(devis.spectacle_duree or "").strip()

        devis.prestation_date = str(devis.prestation_date or "").strip()
        devis.prestation_lieu = str(devis.prestation_lieu or "").strip()
        devis.prestation_adresse = str(devis.prestation_adresse or "").strip()
        devis.prestation_postal_code = str(devis.prestation_postal_code or "").strip()
        devis.prestation_city = str(devis.prestation_city or "").strip()
        devis.prestation_convocation = str(devis.prestation_convocation or "").strip()
        devis.prestation_horaire = str(devis.prestation_horaire or "").strip()

        devis.tva = str(devis.tva or "").strip()
        devis.mode_paiement = str(devis.mode_paiement or "").strip()
        devis.echeance = str(devis.echeance or "").strip()
        devis.date_validite = str(devis.date_validite or "").strip()
        devis.observations = str(devis.observations or "").strip()
        devis.comments = str(devis.comments or "").strip()
        devis.status = devis.status or "draft"

        if not devis.organisateur_structure:
            raise ValueError("L'organisateur est obligatoire.")
        if not devis.spectacle_nom:
            raise ValueError("Le spectacle est obligatoire.")

        try:
            devis.montant = float(devis.montant or 0)
        except (TypeError, ValueError):
            devis.montant = 0.0

        try:
            devis.acompte = float(devis.acompte or 0)
        except (TypeError, ValueError):
            devis.acompte = 0.0

    def _apply_producteur_snapshot(self, devis: Devis) -> None:
        """Copie l'instantane du Producteur actif sur un NOUVEAU devis. Ne doit
        jamais etre appele lors d'une modification : le devis existant conserve
        les informations figees a sa creation, meme si la fiche Producteur change
        ensuite (meme principe que l'instantane des Contrats)."""
        if devis.producteur_id is not None:
            return

        producteur = self.producteur_service.get_active_producteur()
        if producteur is None:
            return

        devis.producteur_id = producteur.id
        devis.producteur_nom = producteur.nom
        devis.producteur_forme_juridique = producteur.forme_juridique
        devis.producteur_adresse = producteur.adresse
        devis.producteur_code_postal = producteur.postal_code
        devis.producteur_ville = producteur.city
        devis.producteur_siret = producteur.siret
        devis.producteur_ape = producteur.ape
        devis.producteur_licence = producteur.licence
        devis.producteur_tva_intracommunautaire = producteur.tva
        devis.producteur_telephone = producteur.phone
        devis.producteur_email = producteur.email
        devis.producteur_site = producteur.site_internet
        devis.producteur_representant = producteur.representant
        devis.producteur_fonction = producteur.fonction
        devis.producteur_iban = producteur.iban
        devis.producteur_bic = producteur.bic
        devis.producteur_logo_path = producteur.logo_path

    def _require(self, devis_id: int) -> Devis:
        devis = self.get_devis(devis_id)
        if devis is None:
            raise ValueError("Devis introuvable.")
        return devis

    def _docx_output_path(self, devis: Devis) -> Path:
        filename = (
            f"{devis.devis_number or self.next_devis_number()} - "
            f"{devis.prestation_date.replace('/', '-')} - "
            f"{devis.organisateur_structure} - "
            f"{devis.spectacle_nom}.docx"
        )
        return self.exports_dir / self._safe_filename(filename)

    def _pdf_output_path(self, devis: Devis) -> Path:
        stem = self._docx_output_path(devis).stem
        return self.exports_dir / f"{stem}.pdf"

    def _safe_filename(self, filename: str) -> str:
        return re.sub(r'[<>:"/\\\\|?*]', "-", filename).strip()

    def _open_path(self, path: Path) -> None:
        import os

        os.startfile(path)

    def _search_text(self, devis: Devis) -> str:
        values = (
            devis.devis_number,
            devis.organisateur_structure,
            devis.organisateur_forme,
            devis.organisateur_adresse,
            devis.organisateur_city,
            devis.organisateur_siret,
            devis.formation_nom,
            devis.spectacle_nom,
            devis.prestation_date,
            devis.prestation_adresse,
            devis.status_label,
        )
        return " ".join(str(value or "") for value in values).casefold()
