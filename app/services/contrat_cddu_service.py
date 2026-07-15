from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

from app.cddu.generator import CdduGenerator
from app.contracts.pdf_converter import PdfConverter
from app.database.database import PROJECT_ROOT
from app.dates import parse_french_date
from app.models.contrat_cddu import ContratCddu
from app.models.contrat_cddu_date import ContratCdduDate
from app.paths import resource_path
from app.repositories.contrat_cddu_repository import ContratCdduRepository
from app.services.artist_service import ArtistService
from app.services.producteur_service import ProducteurService


class ContratCdduService:
    """Couche metier du module Contrat de travail (CDDU) - voir
    docs/CDDU_ARCHITECTURE.md pour la reference complete.

    Sprint 15.0 (fondations techniques) : creation, instantane, numerotation,
    historique, lignes de dates. Sprint 16.0 : generation DOCX/PDF, sur le
    meme modele que ContractService.generate_docx/export_pdf. Aucune UI dans
    les deux cas : uniquement la couche Service."""

    STATUSES = {
        "draft": "Brouillon",
        "validated": "Validé",
        "pdf_generated": "PDF généré",
        "sent": "Envoyé",
        "signed": "Signé",
        "archived": "Archivé",
    }

    def __init__(
        self,
        repository: ContratCdduRepository | None = None,
        producteur_service: ProducteurService | None = None,
        artist_service: ArtistService | None = None,
    ) -> None:
        self.repository = repository or ContratCdduRepository()
        self.producteur_service = producteur_service or ProducteurService()
        self.artist_service = artist_service or ArtistService()
        self.template_path = resource_path("templates", "contrat_cddu.docx")
        self.exports_dir = PROJECT_ROOT / "exports"

    # ===== CRUD contrats_cddu =====

    def list_contrats(self) -> list[ContratCddu]:
        return self.repository.get_all()

    def list_for_prestation(self, prestation_id: int) -> list[ContratCddu]:
        """CDDU dont la prestation de depart est celle-ci. Ne couvre pas les
        CDDU mensualises rattaches uniquement via une ligne contrat_cddu_dates
        (voir list_for_prestation_via_dates) - simple requete croisee, aucune
        duplication de donnee (meme principe que ContractService)."""
        return [contrat for contrat in self.list_contrats() if contrat.prestation_id == prestation_id]

    def list_for_prestation_via_dates(self, prestation_id: int) -> list[ContratCddu]:
        """CDDU couvrant reellement cette prestation via au moins une ligne
        contrat_cddu_dates - source de verite du rattachement pour un CDDU
        mensualise (docs/CDDU_ARCHITECTURE.md §5)."""
        ids = self.repository.contrat_ids_for_prestation_dates(prestation_id)
        return [contrat for contrat in (self.get_contrat(cid) for cid in ids) if contrat is not None]

    def search_contrats(self, query: str = "", status: str = "all") -> list[ContratCddu]:
        normalized_query = query.strip().casefold()
        items = self.list_contrats()

        if status != "all":
            items = [contrat for contrat in items if contrat.status == status]

        if not normalized_query:
            return items

        return [
            contrat
            for contrat in items
            if normalized_query in self._search_text(contrat)
        ]

    def get_contrat(self, contrat_id: int) -> ContratCddu | None:
        return self.repository.get_by_id(contrat_id)

    def build_from_prestation_and_artist(self, prestation, artist_id: int) -> ContratCddu:
        """Prepare un CDDU pre-rempli (producteur actif, artiste, contexte de
        la prestation) sans l'enregistrer - point de depart du workflow
        prioritaire (docs/CDDU_ARCHITECTURE.md §6), une seule date par defaut
        (date_debut de la prestation, 1 cachet)."""
        artist = self.artist_service.get_artist(artist_id)

        contrat = ContratCddu(
            prestation_id=prestation.id,
            artist_id=artist_id,
            prestation_reference=prestation.reference,
            prestation_objet=prestation.nom,
            prestation_lieu=prestation.lieu_nom,
            prestation_ville=prestation.lieu_city,
        )

        if artist is not None:
            contrat.artiste_nom = artist.legal_name or artist.stage_name
            # Prenom toujours copie a part (Sprint 18.2) : le contrat doit
            # afficher le nom complet, jamais le seul nom de famille.
            contrat.artiste_prenom = artist.first_name
            contrat.artiste_adresse = artist.address
            contrat.artiste_postal_code = artist.postal_code
            contrat.artiste_city = artist.city
            contrat.artiste_phone = artist.phone
            contrat.artiste_email = artist.email
            contrat.artiste_date_naissance = artist.birth_date
            contrat.artiste_lieu_naissance = artist.birth_place
            contrat.artiste_numero_secu = artist.social_number
            contrat.artiste_numero_conges_spectacle = artist.conges_spectacle_number
            contrat.artiste_fonction = artist.instrument
            # Categorie professionnelle (Sprint 18.2) : toujours issue de la
            # fiche Artiste, jamais une valeur codee en dur ici ou dans le
            # generateur DOCX.
            contrat.artiste_qualification = artist.qualification

        return contrat

    def create_contrat(self, contrat: ContratCddu) -> int:
        self._prepare(contrat)
        contrat.numero = contrat.numero or self.next_contrat_number()
        self._apply_producteur_snapshot(contrat)
        contrat_id = self.repository.insert(contrat)
        self.repository.add_history(contrat_id, "Creation", "CDDU créé.")
        return contrat_id

    def update_contrat(self, contrat: ContratCddu) -> None:
        if contrat.id is None:
            raise ValueError("Impossible de modifier un CDDU sans identifiant.")

        self._prepare(contrat)
        self.repository.update(contrat)
        self.repository.add_history(contrat.id, "Modification", "CDDU modifié.")

    def delete_contrat(self, contrat_id: int) -> None:
        self.repository.delete(contrat_id)

    def next_contrat_number(self) -> str:
        year = datetime.now().year
        sequence = self.repository.next_sequence(year)
        return f"CDDU-{year}-{sequence:04d}"

    def history(self, contrat_id: int) -> list[dict[str, str]]:
        return self.repository.get_history(contrat_id)

    # ===== Generation DOCX/PDF (Sprint 16.0) =====

    def generate_docx(self, contrat_id: int) -> Path:
        contrat = self._require(contrat_id)
        self._prepare(contrat)
        self._ensure_signature_defaults(contrat)

        dates = self.list_dates(contrat_id)
        output = self._docx_output_path(contrat)
        output.parent.mkdir(exist_ok=True)

        generator = CdduGenerator(self.template_path)
        generator.generate(contrat, dates, str(output))

        self.repository.mark_generated(contrat_id, str(output))
        self.repository.add_history(contrat_id, "Génération DOCX", str(output))
        return output

    def export_pdf(self, contrat_id: int) -> Path:
        docx_path = self.generate_docx(contrat_id)

        contrat = self._require(contrat_id)
        output = self._pdf_output_path(contrat)
        output.parent.mkdir(exist_ok=True)

        PdfConverter().convert(docx_path, output)

        self.repository.mark_pdf_exported(contrat_id, str(output))
        self.repository.add_history(contrat_id, "Export PDF", str(output))

        if contrat.status == "draft":
            # Progression automatique jamais bloquante : Genere PDF avance le
            # statut si le contrat en etait au tout premier stade, mais ne
            # fait jamais reculer un statut deja plus avance (ex. Valide
            # positionne manuellement) - meme principe que
            # PaiementService.compute_facture_status() (docs/CDDU_ARCHITECTURE.md §12).
            # set_status() ne touche que la colonne status : contrairement a
            # update(contrat), il ne risque jamais d'ecraser docx_path/pdf_path
            # avec les valeurs perimees de l'objet en memoire (mark_generated/
            # mark_pdf_exported les ont deja ecrites en base entre-temps).
            self.repository.set_status(contrat_id, "pdf_generated")

        return output

    def open_document(self, contrat_id: int) -> Path:
        contrat = self._require(contrat_id)
        path = Path(contrat.docx_path or "")

        if not path.exists():
            raise FileNotFoundError("Aucun document DOCX généré pour ce CDDU.")

        self._open_path(path)
        self.repository.add_history(contrat_id, "Ouverture DOCX", str(path))
        return path

    def open_pdf(self, contrat_id: int) -> Path:
        contrat = self._require(contrat_id)
        path = Path(contrat.pdf_path or "")

        if not path.exists():
            raise FileNotFoundError("Aucun PDF généré pour ce CDDU.")

        self._open_path(path)
        self.repository.add_history(contrat_id, "Ouverture PDF", str(path))
        return path

    def preview(self, contrat: ContratCddu) -> str:
        dates = self.list_dates(contrat.id) if contrat.id is not None else []
        total_cachets = sum(date.nombre_cachets for date in dates)
        date_lines = (
            "\n".join(f"  - {date.date_travaillee} ({date.nombre_cachets} cachet(s))" for date in dates)
            or "  (aucune date enregistrée)"
        )

        lines = [
            f"Numéro : {contrat.numero or '(automatique)'}",
            f"Employeur : {contrat.producteur_nom or '-'}",
            f"Salarié : {contrat.artiste_nom or '-'}",
            f"Fonction : {contrat.artiste_fonction or '-'}",
            f"Prestation : {contrat.prestation_objet or '-'}",
            f"Lieu : {contrat.prestation_lieu_complet or '-'}",
            "Dates travaillées :",
            date_lines,
            f"Nombre total de cachets : {total_cachets}",
            f"Rémunération brute : {float(contrat.remuneration_brute or 0):.2f} EUR",
        ]

        defraiements = [
            (label, montant)
            for label, montant in (
                ("Déplacement", contrat.defraiement_deplacement),
                ("Hébergement", contrat.defraiement_hebergement),
                ("Repas", contrat.defraiement_repas),
                (contrat.defraiement_autres_libelle or "Autres", contrat.defraiement_autres_montant),
            )
            if float(montant or 0) != 0
        ]
        if defraiements:
            lines.extend(["", "Défraiements"])
            lines.extend(f"  - {label} : {float(montant):.2f} EUR" for label, montant in defraiements)

        lines.extend(["", f"Statut : {self.STATUSES.get(contrat.status, contrat.status)}"])

        if contrat.observations:
            lines.extend(["", "Observations", str(contrat.observations)])

        return "\n".join(lines)

    def _search_text(self, contrat: ContratCddu) -> str:
        values = (
            contrat.numero,
            contrat.artiste_nom,
            contrat.artiste_fonction,
            contrat.prestation_reference,
            contrat.prestation_objet,
            contrat.status_label,
        )
        return " ".join(str(value or "") for value in values).casefold()

    # ===== contrat_cddu_dates =====

    def add_date(self, contrat_id: int, date_travaillee: str, prestation_id: int | None = None, nombre_cachets: int = 1) -> int:
        self._require(contrat_id)
        date_id = self.repository.add_date(
            ContratCdduDate(
                contrat_cddu_id=contrat_id,
                prestation_id=prestation_id,
                date_travaillee=date_travaillee,
                nombre_cachets=nombre_cachets or 1,
            )
        )
        self.repository.add_history(contrat_id, "Ajout d'une date", date_travaillee)
        return date_id

    def list_dates(self, contrat_id: int) -> list[ContratCdduDate]:
        return self.repository.list_dates(contrat_id)

    def remove_date(self, contrat_id: int, date_id: int) -> None:
        self.repository.delete_date(date_id)
        self.repository.add_history(contrat_id, "Suppression d'une date", str(date_id))

    def total_cachets(self, contrat_id: int) -> int:
        """Toujours calcule, jamais stocke (docs/CDDU_ARCHITECTURE.md §5)."""
        return sum(date.nombre_cachets for date in self.list_dates(contrat_id))

    def date_range(self, contrat_id: int) -> tuple[str, str]:
        """Date de debut/fin derivees (min/max) des lignes de dates - jamais
        stockees separement sur le contrat.

        Tri sur la date chronologique reelle (parse_french_date), pas sur le
        texte JJ/MM/AAAA lui-meme : un tri texte classerait par exemple
        "05/01/2026" avant "20/12/2025" (v1.0.3, BUG-001). Une ligne dont la
        date ne se parse pas (jamais le cas en usage normal, cf.
        ContratCdduDate) est ignorée pour le calcul du min/max plutot que de
        faire echouer l'affichage."""
        raw_dates = [date.date_travaillee for date in self.list_dates(contrat_id) if date.date_travaillee]
        parsed = sorted(
            (parse_french_date(raw), raw) for raw in raw_dates if parse_french_date(raw) is not None
        )
        if not parsed:
            return "", ""
        return parsed[0][1], parsed[-1][1]

    def is_mensualise(self, contrat_id: int) -> bool:
        """Type de contrat jamais stocke : derive du nombre de lignes et du
        nombre de prestations distinctes couvertes (docs/CDDU_ARCHITECTURE.md
        §3 et §5)."""
        dates = self.list_dates(contrat_id)
        prestations = {date.prestation_id for date in dates if date.prestation_id is not None}
        return len(dates) > 1 or len(prestations) > 1

    # ===== Internes =====

    def _prepare(self, contrat: ContratCddu) -> None:
        contrat.artiste_nom = str(contrat.artiste_nom or "").strip()
        contrat.artiste_prenom = str(contrat.artiste_prenom or "").strip()
        contrat.artiste_adresse = str(contrat.artiste_adresse or "").strip()
        contrat.artiste_postal_code = str(contrat.artiste_postal_code or "").strip()
        contrat.artiste_city = str(contrat.artiste_city or "").strip()
        contrat.artiste_phone = str(contrat.artiste_phone or "").strip()
        contrat.artiste_email = str(contrat.artiste_email or "").strip()
        contrat.artiste_date_naissance = str(contrat.artiste_date_naissance or "").strip()
        contrat.artiste_lieu_naissance = str(contrat.artiste_lieu_naissance or "").strip()
        contrat.artiste_numero_secu = str(contrat.artiste_numero_secu or "").strip()
        contrat.artiste_numero_conges_spectacle = str(contrat.artiste_numero_conges_spectacle or "").strip()
        contrat.artiste_fonction = str(contrat.artiste_fonction or "").strip()
        contrat.artiste_qualification = str(contrat.artiste_qualification or "").strip()

        contrat.prestation_reference = str(contrat.prestation_reference or "").strip()
        contrat.prestation_objet = str(contrat.prestation_objet or "").strip()
        contrat.prestation_lieu = str(contrat.prestation_lieu or "").strip()
        contrat.prestation_ville = str(contrat.prestation_ville or "").strip()

        # Toujours vide a ce stade : aucune logique de calcul ou de
        # generation (docs/CDDU_ARCHITECTURE.md §9), quelle que soit la
        # valeur transmise.
        contrat.numero_objet = ""

        contrat.observations = str(contrat.observations or "").strip()
        contrat.ville_signature = str(contrat.ville_signature or "").strip()
        contrat.date_signature = str(contrat.date_signature or "").strip()
        contrat.status = contrat.status or "draft"

        if contrat.artist_id is None and not contrat.artiste_nom:
            raise ValueError("Un artiste (salarié) est obligatoire pour creer un CDDU.")

        contrat.remuneration_brute = self._to_float(contrat.remuneration_brute)
        contrat.defraiement_deplacement = self._to_float(contrat.defraiement_deplacement)
        contrat.defraiement_hebergement = self._to_float(contrat.defraiement_hebergement)
        contrat.defraiement_repas = self._to_float(contrat.defraiement_repas)
        contrat.defraiement_autres_montant = self._to_float(contrat.defraiement_autres_montant)
        contrat.defraiement_montant_libre_montant = self._to_float(contrat.defraiement_montant_libre_montant)
        contrat.defraiement_autres_libelle = str(contrat.defraiement_autres_libelle or "").strip()
        contrat.defraiement_montant_libre_libelle = str(contrat.defraiement_montant_libre_libelle or "").strip()

    def _apply_producteur_snapshot(self, contrat: ContratCddu) -> None:
        """Copie l'instantane du Producteur actif sur un NOUVEAU CDDU. Ne
        doit jamais être appele lors d'une modification : le contrat garde
        les informations figees a sa creation, meme si la fiche Producteur
        change ensuite (meme principe que ContractService)."""
        if contrat.producteur_id is not None:
            return

        producteur = self.producteur_service.get_active_producteur()
        if producteur is None:
            return

        contrat.producteur_id = producteur.id
        contrat.producteur_nom = producteur.nom
        contrat.producteur_forme_juridique = producteur.forme_juridique
        contrat.producteur_adresse = producteur.adresse
        contrat.producteur_postal_code = producteur.postal_code
        contrat.producteur_city = producteur.city
        contrat.producteur_siret = producteur.siret
        contrat.producteur_ape = producteur.ape
        contrat.producteur_licence = producteur.licence
        contrat.producteur_convention_collective = producteur.convention_collective
        contrat.producteur_representant = producteur.representant
        contrat.producteur_fonction = producteur.fonction
        contrat.producteur_email = producteur.email
        contrat.producteur_phone = producteur.phone

    def _require(self, contrat_id: int) -> ContratCddu:
        contrat = self.get_contrat(contrat_id)
        if contrat is None:
            raise ValueError("CDDU introuvable.")
        return contrat

    def _ensure_signature_defaults(self, contrat: ContratCddu) -> None:
        """Complete ville_signature/date_signature une seule fois, a la
        premiere generation, puis persiste - jamais recalcule ensuite (meme
        principe d'instantane fige que le reste du contrat) : regenerer le
        DOCX plus tard ne doit jamais afficher une date differente."""
        if contrat.ville_signature and contrat.date_signature:
            return

        changed = False
        if not contrat.ville_signature:
            contrat.ville_signature = contrat.producteur_city
            changed = True
        if not contrat.date_signature:
            contrat.date_signature = datetime.now().strftime("%d/%m/%Y")
            changed = True

        if changed and contrat.id is not None:
            self.repository.set_signature_defaults(contrat.id, contrat.ville_signature, contrat.date_signature)

    def _docx_output_path(self, contrat: ContratCddu) -> Path:
        filename = (
            f"{contrat.numero or self.next_contrat_number()} - "
            f"{contrat.artiste_nom}.docx"
        )
        return self.exports_dir / self._safe_filename(filename)

    def _pdf_output_path(self, contrat: ContratCddu) -> Path:
        stem = self._docx_output_path(contrat).stem
        return self.exports_dir / f"{stem}.pdf"

    def _safe_filename(self, filename: str) -> str:
        return re.sub(r'[<>:"/\\|?*]', "-", filename).strip()

    def _open_path(self, path: Path) -> None:
        import os

        os.startfile(path)

    @staticmethod
    def _to_float(value: Any) -> float:
        try:
            return float(value or 0)
        except (TypeError, ValueError):
            return 0.0
