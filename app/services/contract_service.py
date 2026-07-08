from __future__ import annotations

import re
from dataclasses import replace
from datetime import datetime
from pathlib import Path

from app.contracts.generator import ContractGenerator
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
        contract = self._require(contract_id)
        self._prepare(contract)
        output = self._pdf_output_path(contract)
        output.parent.mkdir(exist_ok=True)

        self._write_contract_pdf(contract, output)
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

    def _write_contract_pdf(self, contract: Contract, output: Path) -> None:
        lines = [
            "Contrat YGNT",
            "",
            *self.preview(contract).splitlines(),
            "",
            "Informations spectacle",
            f"Duree : {contract.spectacle_duree or '-'}",
            f"Convocation : {contract.prestation_convocation or '-'}",
            f"Horaire : {contract.prestation_horaire or '-'}",
            f"Mode de paiement : {contract.mode_paiement or '-'}",
            f"Hebergement : {self._yes_no(contract.hebergement)}",
            f"Restauration : {self._yes_no(contract.restauration)}",
            f"Kilometrage : {self._yes_no(contract.kilometrage)}",
        ]

        if contract.comments:
            lines.extend(["", "Commentaires", str(contract.comments)])

        self._write_text_pdf(output, lines)

    def _write_text_pdf(self, output: Path, lines: list[str]) -> None:
        page_width = 595
        page_height = 842
        x = 56
        y = page_height - 64
        line_height = 16
        pages: list[list[str]] = [[]]

        for raw_line in lines:
            wrapped = self._wrap_line(raw_line, 92) or [""]
            for line in wrapped:
                if y < 64:
                    pages.append([])
                    y = page_height - 64
                pages[-1].append(f"BT /F1 10 Tf {x} {y} Td ({self._pdf_escape(line)}) Tj ET")
                y -= line_height

        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            None,
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        ]
        page_refs = []

        for page in pages:
            content = "\n".join(page).encode("latin-1", "replace")
            content_obj = len(objects) + 1
            objects.append(
                b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n"
                + content
                + b"\nendstream"
            )
            page_obj = len(objects) + 1
            page_refs.append(page_obj)
            objects.append(
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {page_width} {page_height}] "
                f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_obj} 0 R >>".encode("ascii")
            )

        kids = " ".join(f"{ref} 0 R" for ref in page_refs)
        objects[1] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_refs)} >>".encode("ascii")

        data = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for index, obj in enumerate(objects, start=1):
            offsets.append(len(data))
            data.extend(f"{index} 0 obj\n".encode("ascii"))
            data.extend(obj or b"")
            data.extend(b"\nendobj\n")

        xref_offset = len(data)
        data.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
        data.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            data.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
        data.extend(
            f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n".encode("ascii")
        )

        output.write_bytes(data)

    def _wrap_line(self, line: str, width: int) -> list[str]:
        text = str(line)
        if len(text) <= width:
            return [text]

        parts = []
        current = ""
        for word in text.split():
            if len(current) + len(word) + 1 > width:
                parts.append(current)
                current = word
            else:
                current = f"{current} {word}".strip()
        if current:
            parts.append(current)
        return parts

    def _pdf_escape(self, text: str) -> str:
        return (
            str(text)
            .encode("latin-1", "replace")
            .decode("latin-1")
            .replace("\\", "\\\\")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )

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

    def _yes_no(self, value: bool) -> str:
        return "Oui" if value else "Non"

    def _open_path(self, path: Path) -> None:
        import os

        os.startfile(path)
