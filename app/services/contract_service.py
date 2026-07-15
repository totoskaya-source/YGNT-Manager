from __future__ import annotations

import re
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from app.contracts.generator import ContractGenerator
from app.contracts.pdf_converter import PdfConverter
from app.database.database import PROJECT_ROOT
from app.models.contract import Contract
from app.models.devis import Devis
from app.models.prestation import Prestation
from app.paths import resource_path
from app.repositories.contract_repository import ContractRepository
from app.services.formation_service import FormationService
from app.services.producteur_service import ProducteurService


class ContractService:
    STATUSES = {
        "draft": "Brouillon",
        "validated": "Validé",
        "signed": "Signé",
    }

    def __init__(
        self,
        repository: ContractRepository | None = None,
        producteur_service: ProducteurService | None = None,
        formation_service: FormationService | None = None,
    ) -> None:
        self.repository = repository or ContractRepository()
        self.producteur_service = producteur_service or ProducteurService()
        self.formation_service = formation_service or FormationService()
        self.template_path = resource_path("templates", "contrat_cession.docx")
        self.exports_dir = PROJECT_ROOT / "exports"

    def list_contracts(self) -> list[Contract]:
        return self.repository.get_all()

    def list_for_prestation(self, prestation_id: int) -> list[Contract]:
        """Contrats rattaches a une prestation (Dossier), via prestation_id
        uniquement : aucune duplication de donnee, simple requete croisee."""
        return [contract for contract in self.list_contracts() if contract.prestation_id == prestation_id]

    def build_from_prestation(self, prestation: Prestation) -> Contract:
        """Prepare un contrat pre-rempli (Formation, organisateur, date, lieu)
        a partir d'une prestation, sans aucune intervention utilisateur
        supplementaire (Sprint 18.1) : le contrat n'est pas enregistré, c'est
        un point de depart, toujours modifiable avant validation.

        Le contrat de cession ne depend plus jamais d'une fiche Artiste : la
        Formation (prestation.formation_id) est l'unique source de l'objet
        vendu. artist_id est conserve tel quel pour compatibilite (une
        prestation ancienne peut ne porter que artist_id), mais n'alimente
        plus aucun champ affiche - seule la Formation le fait desormais.

        Note technique importante : le template contrat_cession.docx n'a
        jamais imprime les champs artiste_* (aucun placeholder {{artiste_*}}
        n'existe dans le document - verifie, pas suppose). Le seul champ
        imprime qui identifie ce qui est vendu est {{spectacle_nom}}. Pour
        que le contrat créé en un clic affiche reellement le nom de la
        Formation sans aucune saisie manuelle, spectacle_nom est ici
        pre-rempli avec le nom de la Formation (reste toujours modifiable
        avant enregistrement, comme tout le reste)."""
        contract = Contract(
            prestation_id=prestation.id,
            artist_id=prestation.artist_id,
            formation_id=prestation.formation_id,
            organization_id=prestation.organization_id,
            prestation_date=prestation.date_debut,
            prestation_lieu=prestation.lieu_nom,
            prestation_adresse=prestation.lieu_adresse,
            prestation_postal_code=prestation.lieu_postal_code,
            prestation_city=prestation.lieu_city,
        )

        if prestation.formation_id is not None:
            self._apply_formation_snapshot(contract, prestation.formation_id)
            contract.spectacle_nom = contract.artiste_nom

        return contract

    def _apply_formation_snapshot(self, contract: Contract, formation_id: int) -> None:
        """Copie les informations de la Formation dans l'instantane
        artiste_* du contrat (reutilise tel quel : meme colonnes, meme
        template DOCX, aucun changement de mise en page). Les champs
        propres a une personne physique (SIREN, numero de sécurité sociale)
        ne sont jamais renseignes : une Formation n'est jamais une personne,
        les musiciens n'apparaissent jamais sur ce contrat."""
        formation = self.formation_service.get_formation(formation_id)
        if formation is None:
            return

        contract.artiste_nom = formation.nom
        contract.artiste_adresse = formation.address
        contract.artiste_postal_code = formation.postal_code
        contract.artiste_city = formation.city
        contract.artiste_phone = formation.phone
        contract.artiste_email = formation.email
        contract.artiste_siret = formation.siret
        contract.artiste_ape = formation.ape
        contract.artiste_licence = formation.licence
        contract.artiste_iban = formation.iban
        contract.artiste_bic = formation.bic

    def build_from_devis(self, devis: Devis) -> Contract:
        """Prepare un contrat pre-rempli (formation, organisateur, objet, date,
        lieu, conditions financières) a partir d'un Devis accepte. Le contrat
        n'est pas enregistré : c'est un nouveau document independant, toujours
        modifiable avant validation. Le Devis n'est jamais modifié (meme
        philosophie que build_from_prestation).

        Le Producteur n'est volontairement pas copie depuis le Devis : comme
        pour tout nouveau contrat, ContractService.create_contract() lui
        appliquera l'instantane du Producteur actif au moment de la creation
        (regle déjà en vigueur depuis le Sprint 8.6).

        Sprint 20 : l'instantane artiste_* du contrat est repris directement
        de l'instantane formation_* deja fige sur le Devis (jamais recalcule
        depuis la Formation/l'Artiste d'origine - le Devis, une fois cree,
        est la source de verite). formation_id n'est reporte sur le contrat
        que s'il correspond reellement a une Formation ; sinon il est
        conserve dans artist_id pour compatibilite (devis ancien)."""
        is_real_formation = (
            devis.formation_id is not None
            and self.formation_service.get_formation(devis.formation_id) is not None
        )
        return Contract(
            prestation_id=devis.prestation_id,
            formation_id=devis.formation_id if is_real_formation else None,
            artist_id=None if is_real_formation else devis.formation_id,
            organization_id=devis.organization_id,
            spectacle_nom=devis.spectacle_nom,
            spectacle_duree=devis.spectacle_duree,
            prestation_date=devis.prestation_date,
            prestation_lieu=devis.prestation_lieu,
            prestation_adresse=devis.prestation_adresse,
            prestation_postal_code=devis.prestation_postal_code,
            prestation_city=devis.prestation_city,
            comments=devis.comments,
            cession_montant=devis.montant,
            cachet_tva=devis.tva,
            acompte=devis.acompte,
            mode_paiement=devis.mode_paiement,
            echeance=devis.echeance,
            artiste_nom=devis.formation_nom,
            artiste_adresse=devis.formation_adresse,
            artiste_postal_code=devis.formation_postal_code,
            artiste_city=devis.formation_city,
            artiste_phone=devis.formation_phone,
            artiste_email=devis.formation_email,
            artiste_siret=devis.formation_siret,
            artiste_ape=devis.formation_ape,
            artiste_licence=devis.formation_licence,
            artiste_iban=devis.formation_iban,
            artiste_bic=devis.formation_bic,
        )

    def search_contracts(self, query: str = "", status: str = "all") -> list[Contract]:
        normalized_query = query.strip().casefold()
        contracts = self.list_contracts()

        if status != "all":
            contracts = [contract for contract in contracts if contract.status == status]

        if not normalized_query:
            return contracts

        return [
            contract
            for contract in contracts
            if normalized_query in self._search_text(contract)
        ]

    def get_contract(self, contract_id: int) -> Contract | None:
        return self.repository.get_by_id(contract_id)

    def create_contract(self, contract: Contract) -> int:
        self._prepare(contract)
        contract.contract_number = contract.contract_number or self.next_contract_number()
        self._apply_producteur_snapshot(contract)
        contract_id = self.repository.insert(contract)
        self.repository.add_history(contract_id, "Creation", "Contrat créé.")
        return contract_id

    def update_contract(self, contract: Contract) -> None:
        if contract.id is None:
            raise ValueError("Impossible de modifier un contrat sans identifiant.")

        self._prepare(contract)
        self.repository.update(contract)
        self.repository.add_history(contract.id, "Modification", "Contrat modifié.")

    def duplicate_contract(self, contract_id: int) -> int:
        contract = self._require(contract_id)
        duplicate = replace(
            contract,
            id=None,
            contract_number=self.next_contract_number(),
            status="draft",
            docx_path="",
            pdf_path="",
            created_at=None,
            updated_at=None,
            generated_at=None,
        )
        new_id = self.repository.insert(duplicate)
        self.repository.add_history(
            new_id,
            "Duplication",
            f"Copie du contrat {contract.contract_number or contract.id}.",
        )
        return new_id

    def delete_contract(self, contract_id: int) -> None:
        self.repository.delete(contract_id)

    def generate_docx(self, contract_id: int) -> Path:
        contract = self._require(contract_id)
        self._prepare(contract)
        output = self._docx_output_path(contract)
        output.parent.mkdir(exist_ok=True)

        generator = ContractGenerator(self.template_path)
        generator.generate(contract, str(output))

        self.repository.mark_generated(contract_id, str(output))
        self.repository.add_history(contract_id, "Génération DOCX", str(output))
        return output

    def export_pdf(self, contract_id: int) -> Path:
        docx_path = self.generate_docx(contract_id)

        contract = self._require(contract_id)
        output = self._pdf_output_path(contract)
        output.parent.mkdir(exist_ok=True)

        PdfConverter().convert(docx_path, output)

        self.repository.mark_pdf_exported(contract_id, str(output))
        self.repository.add_history(contract_id, "Export PDF", str(output))
        return output

    def open_document(self, contract_id: int) -> Path:
        contract = self._require(contract_id)
        path = Path(contract.docx_path or "")

        if not path.exists():
            raise FileNotFoundError("Aucun document DOCX généré pour ce contrat.")

        self._open_path(path)
        self.repository.add_history(contract_id, "Ouverture DOCX", str(path))
        return path

    def open_pdf(self, contract_id: int) -> Path:
        contract = self._require(contract_id)
        path = Path(contract.pdf_path or "")

        if not path.exists():
            raise FileNotFoundError("Aucun PDF généré pour ce contrat.")

        self._open_path(path)
        self.repository.add_history(contract_id, "Ouverture PDF", str(path))
        return path

    def history(self, contract_id: int) -> list[dict[str, str]]:
        return self.repository.get_history(contract_id)

    def next_contract_number(self) -> str:
        year = datetime.now().year
        sequence = self.repository.next_sequence(year)
        return f"YGNT-{year}-{sequence:04d}"

    def preview(self, contract: Contract) -> str:
        self._prepare(contract)
        lines = [
            f"Numéro : {contract.contract_number or '(automatique)'}",
            f"Producteur : {contract.producteur_nom or '-'}",
            f"Forme juridique (producteur) : {contract.producteur_forme_juridique or '-'}",
            f"Adresse producteur : {self._producer_address(contract) or '-'}",
            f"SIRET producteur : {contract.producteur_siret or '-'}",
            f"Licence producteur : {contract.producteur_licence or '-'}",
            f"Représenté par (producteur) : {contract.producteur_representant or '-'}",
            f"Fonction (producteur) : {contract.producteur_fonction or '-'}",
            f"Artiste : {contract.artiste_nom or '-'}",
            f"Organisateur : {contract.organisateur_structure or '-'}",
            f"Forme juridique : {contract.organisateur_forme or '-'}",
            f"Adresse organisateur : {self._organizer_address(contract) or '-'}",
            f"SIRET : {contract.organisateur_siret or '-'}",
            f"Code APE : {contract.organisateur_ape or '-'}",
            f"Licence : {contract.organisateur_licence or '-'}",
            f"TVA intracommunautaire : {contract.organisateur_tva or '-'}",
            f"Téléphone : {contract.organisateur_phone or '-'}",
            f"Email : {contract.organisateur_email or '-'}",
            f"Représentant : {contract.organisateur_representant or '-'}",
            f"Fonction : {contract.organisateur_fonction or '-'}",
            f"Spectacle : {contract.spectacle_nom or '-'}",
            f"Date : {contract.prestation_date or '-'}",
            f"Lieu de la prestation : {contract.prestation_lieu_complet or '-'}",
            f"Durée : {contract.spectacle_duree or '-'}",
            f"Cachet : {float(contract.cession_montant or 0):.2f} EUR",
            f"Acompte : {float(contract.acompte or 0):.2f} EUR",
            f"TVA : {contract.cachet_tva or '-'}",
            f"Mode de paiement : {contract.mode_paiement or '-'}",
            f"Échéance : {contract.echeance or '-'}",
            f"Statut : {self.STATUSES.get(contract.status, contract.status)}",
        ]

        if contract.observations:
            lines.extend(["", "Observations", str(contract.observations)])
        if contract.comments:
            lines.extend(["", "Notes", str(contract.comments)])

        return "\n".join(lines)

    def _prepare(self, contract: Contract) -> None:
        contract.producteur_nom = str(contract.producteur_nom or "").strip()
        contract.producteur_forme_juridique = str(contract.producteur_forme_juridique or "").strip()
        contract.producteur_adresse = str(contract.producteur_adresse or "").strip()
        contract.producteur_code_postal = str(contract.producteur_code_postal or "").strip()
        contract.producteur_ville = str(contract.producteur_ville or "").strip()
        contract.producteur_siret = str(contract.producteur_siret or "").strip()
        contract.producteur_ape = str(contract.producteur_ape or "").strip()
        contract.producteur_licence = str(contract.producteur_licence or "").strip()
        contract.producteur_tva_intracommunautaire = str(contract.producteur_tva_intracommunautaire or "").strip()
        contract.producteur_telephone = str(contract.producteur_telephone or "").strip()
        contract.producteur_email = str(contract.producteur_email or "").strip()
        contract.producteur_site = str(contract.producteur_site or "").strip()
        contract.producteur_representant = str(contract.producteur_representant or "").strip()
        contract.producteur_fonction = str(contract.producteur_fonction or "").strip()
        contract.producteur_iban = str(contract.producteur_iban or "").strip()
        contract.producteur_bic = str(contract.producteur_bic or "").strip()
        contract.organisateur_structure = str(contract.organisateur_structure or "").strip()
        contract.organisateur_forme = str(contract.organisateur_forme or "").strip()
        contract.organisateur_adresse = str(contract.organisateur_adresse or "").strip()
        contract.organisateur_postal_code = str(contract.organisateur_postal_code or "").strip()
        contract.organisateur_city = str(contract.organisateur_city or "").strip()
        contract.organisateur_siret = str(contract.organisateur_siret or "").strip()
        contract.organisateur_phone = str(contract.organisateur_phone or "").strip()
        contract.organisateur_email = str(contract.organisateur_email or "").strip()
        contract.organisateur_ape = str(contract.organisateur_ape or "").strip()
        contract.organisateur_licence = str(contract.organisateur_licence or "").strip()
        contract.organisateur_tva = str(contract.organisateur_tva or "").strip()
        contract.organisateur_representant = str(contract.organisateur_representant or "").strip()
        contract.organisateur_fonction = str(contract.organisateur_fonction or "").strip()
        contract.organisateur_iban = str(contract.organisateur_iban or "").strip()
        contract.organisateur_bic = str(contract.organisateur_bic or "").strip()
        contract.organisateur_site_internet = str(contract.organisateur_site_internet or "").strip()
        contract.organisateur_notes = str(contract.organisateur_notes or "").strip()
        contract.artiste_nom = str(contract.artiste_nom or "").strip()
        contract.artiste_adresse = str(contract.artiste_adresse or "").strip()
        contract.artiste_postal_code = str(contract.artiste_postal_code or "").strip()
        contract.artiste_city = str(contract.artiste_city or "").strip()
        contract.artiste_phone = str(contract.artiste_phone or "").strip()
        contract.artiste_email = str(contract.artiste_email or "").strip()
        contract.artiste_siren = str(contract.artiste_siren or "").strip()
        contract.artiste_siret = str(contract.artiste_siret or "").strip()
        contract.artiste_ape = str(contract.artiste_ape or "").strip()
        contract.artiste_licence = str(contract.artiste_licence or "").strip()
        contract.artiste_iban = str(contract.artiste_iban or "").strip()
        contract.artiste_bic = str(contract.artiste_bic or "").strip()
        contract.artiste_social_number = str(contract.artiste_social_number or "").strip()
        contract.artiste_notes = str(contract.artiste_notes or "").strip()
        contract.spectacle_nom = str(contract.spectacle_nom or "").strip()
        contract.prestation_lieu = str(contract.prestation_lieu or "").strip()
        contract.prestation_adresse = str(contract.prestation_adresse or "").strip()
        contract.prestation_postal_code = str(contract.prestation_postal_code or "").strip()
        contract.prestation_city = str(contract.prestation_city or "").strip()
        contract.prestation_date = str(contract.prestation_date or "").strip()
        contract.spectacle_duree = str(contract.spectacle_duree or "").strip()
        contract.prestation_convocation = str(contract.prestation_convocation or "").strip()
        contract.prestation_horaire = str(contract.prestation_horaire or "").strip()
        contract.cachet_tva = str(contract.cachet_tva or "").strip()
        contract.echeance = str(contract.echeance or "").strip()
        contract.observations = str(contract.observations or "").strip()
        contract.mode_paiement = str(contract.mode_paiement or "").strip()
        contract.status = contract.status or "draft"

        if not contract.organisateur_structure:
            raise ValueError("L'organisateur est obligatoire.")
        if not contract.spectacle_nom:
            raise ValueError("Le spectacle est obligatoire.")

        contract.event_name = contract.event_name or contract.spectacle_nom
        contract.venue = contract.venue or contract.prestation_lieu or contract.prestation_adresse
        contract.event_date = contract.event_date or contract.prestation_date

        try:
            contract.cession_montant = float(contract.cession_montant or 0)
        except (TypeError, ValueError):
            contract.cession_montant = 0.0
        contract.gross_salary = contract.gross_salary or float(contract.cession_montant)

        try:
            contract.acompte = float(contract.acompte or 0)
        except (TypeError, ValueError):
            contract.acompte = 0.0

    def _require(self, contract_id: int) -> Contract:
        contract = self.get_contract(contract_id)
        if contract is None:
            raise ValueError("Contrat introuvable.")
        return contract

    def _search_text(self, contract: Contract) -> str:
        values = (
            contract.contract_number,
            contract.organisateur_structure,
            contract.organisateur_forme,
            contract.organisateur_adresse,
            contract.organisateur_postal_code,
            contract.organisateur_city,
            contract.organisateur_siret,
            contract.organisateur_phone,
            contract.organisateur_email,
            contract.organisateur_ape,
            contract.organisateur_licence,
            contract.organisateur_tva,
            contract.organisateur_representant,
            contract.organisateur_fonction,
            contract.artiste_nom,
            contract.spectacle_nom,
            contract.prestation_date,
            contract.prestation_adresse,
            contract.status_label,
            contract.docx_path,
        )
        return " ".join(str(value or "") for value in values).casefold()

    def _docx_output_path(self, contract: Contract) -> Path:
        filename = (
            f"{contract.contract_number or self.next_contract_number()} - "
            f"{contract.prestation_date.replace('/', '-')} - "
            f"{contract.organisateur_structure} - "
            f"{contract.spectacle_nom}.docx"
        )
        return self.exports_dir / self._safe_filename(filename)

    def _pdf_output_path(self, contract: Contract) -> Path:
        stem = self._docx_output_path(contract).stem
        return self.exports_dir / f"{stem}.pdf"

    def _safe_filename(self, filename: str) -> str:
        return re.sub(r'[<>:"/\\\\|?*]', "-", filename).strip()

    def _organizer_address(self, contract: Contract) -> str:
        return " ".join(
            part
            for part in (
                contract.organisateur_adresse,
                contract.organisateur_postal_code,
                contract.organisateur_city,
            )
            if part
        )

    def _producer_address(self, contract: Contract) -> str:
        return " ".join(
            part
            for part in (
                contract.producteur_adresse,
                contract.producteur_code_postal,
                contract.producteur_ville,
            )
            if part
        )

    def _apply_producteur_snapshot(self, contract: Contract) -> None:
        """Copie l'instantane du Producteur actif sur un NOUVEAU contrat. Ne doit
        jamais être appele lors d'une modification : le contrat existant conserve
        les informations figees a sa creation, meme si la fiche Producteur change
        ensuite (meme principe que l'instantane organisateur/artiste)."""
        if contract.producteur_id is not None:
            return

        producteur = self.producteur_service.get_active_producteur()
        if producteur is None:
            return

        contract.producteur_id = producteur.id
        contract.producteur_nom = producteur.nom
        contract.producteur_forme_juridique = producteur.forme_juridique
        contract.producteur_adresse = producteur.adresse
        contract.producteur_code_postal = producteur.postal_code
        contract.producteur_ville = producteur.city
        contract.producteur_siret = producteur.siret
        contract.producteur_ape = producteur.ape
        contract.producteur_licence = producteur.licence
        contract.producteur_tva_intracommunautaire = producteur.tva
        contract.producteur_telephone = producteur.phone
        contract.producteur_email = producteur.email
        contract.producteur_site = producteur.site_internet
        contract.producteur_representant = producteur.representant
        contract.producteur_fonction = producteur.fonction
        contract.producteur_iban = producteur.iban
        contract.producteur_bic = producteur.bic

    def _open_path(self, path: Path) -> None:
        import os

        os.startfile(path)
