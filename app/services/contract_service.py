from __future__ import annotations

import re
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from app.contracts.generator import ContractGenerator
from app.contracts.pdf_converter import PdfConverter
from app.database.database import PROJECT_ROOT
from app.models.contract import Contract
from app.repositories.contract_repository import ContractRepository


class ContractService:
    STATUSES = {
        "draft": "Brouillon",
        "validated": "Valide",
        "signed": "Signe",
    }

    def __init__(self, repository: ContractRepository | None = None) -> None:
        self.repository = repository or ContractRepository()
        self.template_path = PROJECT_ROOT / "templates" / "contrat_cession.docx"
        self.exports_dir = PROJECT_ROOT / "exports"

    def list_contracts(self) -> list[Contract]:
        return self.repository.get_all()

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
        contract_id = self.repository.insert(contract)
        self.repository.add_history(contract_id, "Creation", "Contrat cree.")
        return contract_id

    def update_contract(self, contract: Contract) -> None:
        if contract.id is None:
            raise ValueError("Impossible de modifier un contrat sans identifiant.")

        self._prepare(contract)
        self.repository.update(contract)
        self.repository.add_history(contract.id, "Modification", "Contrat modifie.")

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
        self.repository.add_history(contract_id, "Generation DOCX", str(output))
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
            raise FileNotFoundError("Aucun document DOCX genere pour ce contrat.")

        self._open_path(path)
        self.repository.add_history(contract_id, "Ouverture DOCX", str(path))
        return path

    def open_pdf(self, contract_id: int) -> Path:
        contract = self._require(contract_id)
        path = Path(contract.pdf_path or "")

        if not path.exists():
            raise FileNotFoundError("Aucun PDF genere pour ce contrat.")

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
            f"Numero : {contract.contract_number or '(automatique)'}",
            f"Organisateur : {contract.organisateur_structure or '-'}",
            f"Forme juridique : {contract.organisateur_forme or '-'}",
            f"Adresse organisateur : {self._organizer_address(contract) or '-'}",
            f"SIRET : {contract.organisateur_siret or '-'}",
            f"Code APE : {contract.organisateur_ape or '-'}",
            f"Licence : {contract.organisateur_licence or '-'}",
            f"TVA intracommunautaire : {contract.organisateur_tva or '-'}",
            f"Telephone : {contract.organisateur_phone or '-'}",
            f"Email : {contract.organisateur_email or '-'}",
            f"Representant : {contract.organisateur_representant or '-'}",
            f"Fonction : {contract.organisateur_fonction or '-'}",
            f"Spectacle : {contract.spectacle_nom or '-'}",
            f"Date : {contract.prestation_date or '-'}",
            f"Lieu : {contract.prestation_adresse or '-'}",
            f"Montant : {float(contract.cession_montant or 0):.2f} EUR",
            f"Statut : {self.STATUSES.get(contract.status, contract.status)}",
        ]
        return "\n".join(lines)

    def _prepare(self, contract: Contract) -> None:
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
        contract.prestation_adresse = str(contract.prestation_adresse or "").strip()
        contract.prestation_date = str(contract.prestation_date or "").strip()
        contract.spectacle_duree = str(contract.spectacle_duree or "").strip()
        contract.prestation_convocation = str(contract.prestation_convocation or "").strip()
        contract.prestation_horaire = str(contract.prestation_horaire or "").strip()
        contract.mode_paiement = str(contract.mode_paiement or "").strip()
        contract.status = contract.status or "draft"

        if not contract.organisateur_structure:
            raise ValueError("L'organisateur est obligatoire.")
        if not contract.spectacle_nom:
            raise ValueError("Le spectacle est obligatoire.")

        contract.event_name = contract.event_name or contract.spectacle_nom
        contract.venue = contract.venue or contract.prestation_adresse
        contract.event_date = contract.event_date or contract.prestation_date

        try:
            contract.cession_montant = float(contract.cession_montant or 0)
        except (TypeError, ValueError):
            contract.cession_montant = 0.0
        contract.gross_salary = contract.gross_salary or float(contract.cession_montant)

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

    def _open_path(self, path: Path) -> None:
        import os

        os.startfile(path)
