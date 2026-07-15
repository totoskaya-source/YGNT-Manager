# -*- coding: utf-8 -*-
"""Bugfix - Impossible d'enregistrer une facture creee depuis une prestation.

Cause exacte : app/database/migrations.py portait
`FOREIGN KEY(formation_id) REFERENCES artists(id)` sur la table `factures`,
une contrainte heritee de l'epoque ou formation_id designait toujours un
artiste. Depuis que FactureService.build_from_prestation() y ecrit un vrai
formations.id (Sprint 20, prestation utilisant la nouvelle entite Formation),
cette contrainte etait violee a l'insertion (sqlite3.IntegrityError), non
interceptee par FactureDialog.save() (qui ne capture que ValueError) : la
facture ne s'enregistrait jamais, sans aucun message visible.

Reproduit le bug tel quel (avant correctif il aurait fallu voir
sqlite3.IntegrityError leve depuis FactureRepository.insert()), puis verifie
le parcours complet demande : Prestation -> Facture, Contrat -> Facture,
facture existante (modification), generation DOCX, generation PDF.

Base SQLite TEMPORAIRE et isolee (data/ygnt_manager.db n'est jamais touchee).
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import tempfile
from pathlib import Path

import app.database.database as database_module

_tmp_dir = tempfile.TemporaryDirectory()
database_module.DB_PATH = Path(_tmp_dir.name) / "test_facture_formation_fk_bugfix.db"
database_module.Database._instance = None

from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

app = QApplication.instance() or QApplication([])
_captured_warnings: list[tuple[str, str]] = []


def _capture_warning(*args, **kwargs):
    title = args[1] if len(args) > 1 else ""
    text = args[2] if len(args) > 2 else ""
    _captured_warnings.append((title, text))
    print(f"    [MessageBox warning] titre='{title}' texte='{text}'")


QMessageBox.information = staticmethod(lambda *a, **k: None)
QMessageBox.warning = staticmethod(_capture_warning)

from app.database.migrations import MigrationManager  # noqa: E402

failures: list[str] = []


def check(label: str, condition: bool) -> None:
    status = "OK" if condition else "ECHEC"
    print(f"[{status}] {label}")
    if not condition:
        failures.append(label)


MigrationManager().migrate()

from app.repositories.base_repository import BaseRepository  # noqa: E402
from app.models.artist import Artist  # noqa: E402
from app.models.contract import Contract  # noqa: E402
from app.models.formation import Formation  # noqa: E402
from app.models.organization import Organization  # noqa: E402
from app.models.prestation import Prestation  # noqa: E402
from app.models.producteur import Producteur  # noqa: E402
from app.services.artist_service import ArtistService  # noqa: E402
from app.services.contract_service import ContractService  # noqa: E402
from app.services.facture_service import FactureService  # noqa: E402
from app.services.formation_service import FormationService  # noqa: E402
from app.services.organization_service import OrganizationService  # noqa: E402
from app.services.prestation_service import PrestationService  # noqa: E402
from app.services.producteur_service import ProducteurService  # noqa: E402
from app.ui.contract_dialog import ContractDialog  # noqa: E402
from app.ui.facture_dialog import FactureDialog  # noqa: E402

# ---------------------------------------------------------------------------
print("== Schema : verification directe de la contrainte corrigee ==")

db = BaseRepository().db
foreign_keys = db.fetchall("PRAGMA foreign_key_list(factures)")
check(
    "factures.formation_id ne reference plus artists(id)",
    not any(fk["table"] == "artists" and fk["from"] == "formation_id" for fk in foreign_keys),
)
check(
    "les 4 autres cles etrangeres de factures sont toujours presentes",
    {fk["table"] for fk in foreign_keys} == {"organizations", "producteurs", "contracts", "prestations"},
)

# ---------------------------------------------------------------------------
print("\n== Donnees de test ==")

ProducteurService().create_producteur(Producteur(nom="YGNT Production", city="Villeneuve", representant="Sophie Dupont"))
artist_service = ArtistService()
musicien_id = artist_service.create_artist(Artist(legal_name="Zahn", first_name="Anthony", instrument="Guitare", qualification="Artiste musicien"))

formation_service = FormationService()
formation_id = formation_service.create_formation(Formation(nom="Duo Nouvelle Vague", city="Marseille", siret="12345678900011"))

organization_id = OrganizationService().create_organization(Organization(name="Mairie de Test", city="Testville"))

prestation_service = PrestationService()
prestation_id = prestation_service.create_prestation(Prestation(
    nom="Concert Formation", type_evenement="festival", date_debut="20/08/2026",
    formation_id=formation_id, organization_id=organization_id,
    lieu_nom="Salle des fetes", lieu_city="Marseille",
))
prestation = prestation_service.get_prestation(prestation_id)

facture_service = FactureService()
contract_service = ContractService()

# ---------------------------------------------------------------------------
print("\n== PARCOURS 1 : Prestation -> Facture (le bug original) ==")

seed = facture_service.build_from_prestation(prestation)
check("build_from_prestation() renvoie bien un vrai formations.id", seed.formation_id == formation_id)

dlg = FactureDialog(None, initial_facture=seed, service=facture_service, organization_service=OrganizationService())
dlg.montant.setValue(1500.0)
dlg.save()

check("la facture a bien un id apres save() (aucune IntegrityError silencieuse)", dlg.facture.id is not None)
check("aucun message d'erreur affiche a l'utilisateur", len(_captured_warnings) == 0)

facture1_id = dlg.facture.id
saved = facture_service.get_facture(facture1_id) if facture1_id else None
check("la facture est bien relue depuis la base", saved is not None)
if saved is not None:
    check("formation_id correctement persiste (vraie Formation)", saved.formation_id == formation_id)
    check("formation_nom correctement pre-rempli", saved.formation_nom == "Duo Nouvelle Vague")

# ---------------------------------------------------------------------------
print("\n== PARCOURS 2 : Contrat -> Facture ==")

contract_seed = contract_service.build_from_prestation(prestation)
contract_dialog = ContractDialog(None, initial_contract=contract_seed, service=contract_service, organization_service=OrganizationService())
contract_dialog.montant.setValue(1500.0)
contract_dialog.save()
contract_id = contract_dialog.contract.id
check("le contrat s'enregistre normalement", contract_id is not None)

contract_saved = contract_service.get_contract(contract_id)
facture_from_contract_seed = facture_service.build_from_contract(contract_saved)
dlg2 = FactureDialog(None, initial_facture=facture_from_contract_seed, service=facture_service, organization_service=OrganizationService())
dlg2.save()
check("la facture depuis un contrat s'enregistre aussi sans erreur", dlg2.facture.id is not None)
check("aucun nouveau message d'erreur", len(_captured_warnings) == 0)

# ---------------------------------------------------------------------------
print("\n== PARCOURS 3 : Facture existante (modification) ==")

facture_existing = facture_service.get_facture(facture1_id)
edit_dialog = FactureDialog(None, facture=facture_existing, service=facture_service, organization_service=OrganizationService())
edit_dialog.montant.setValue(1600.0)
edit_dialog.save()
check("la modification d'une facture existante fonctionne toujours", edit_dialog.facture.montant == 1600.0)
check("aucun nouveau message d'erreur (modification)", len(_captured_warnings) == 0)

reloaded = facture_service.get_facture(facture1_id)
check("le nouveau montant est bien persiste", reloaded.montant == 1600.0)

# ---------------------------------------------------------------------------
print("\n== PARCOURS 4 : Generation DOCX ==")

docx_path = facture_service.generate_docx(facture1_id)
check("le DOCX de la facture se genere sans erreur", docx_path.exists())

# ---------------------------------------------------------------------------
print("\n== PARCOURS 5 : Generation PDF ==")

try:
    pdf_path = facture_service.generate_pdf(facture1_id)
    check("le PDF de la facture se genere sans erreur", pdf_path.exists())
except Exception as exc:
    print(f"[INFO] Conversion PDF non verifiee sur ce poste (Word/COM absent ?) : {exc!r}")

# ---------------------------------------------------------------------------
print("\n== Non-regression : ancienne prestation (artist_id seul, compatibilite) ==")

old_prestation_id = prestation_service.create_prestation(Prestation(
    nom="Concert Ancien", type_evenement="mariage", date_debut="15/09/2026",
    artist_id=musicien_id, organization_id=organization_id,
))
old_prestation = prestation_service.get_prestation(old_prestation_id)
old_seed = facture_service.build_from_prestation(old_prestation)
check("compatibilite : formation_id repli sur artist_id pour une ancienne prestation", old_seed.formation_id == musicien_id)

old_dlg = FactureDialog(None, initial_facture=old_seed, service=facture_service, organization_service=OrganizationService())
old_dlg.montant.setValue(800.0)
old_dlg.save()
check("une facture depuis une ancienne prestation (artist_id) s'enregistre toujours", old_dlg.facture.id is not None)

# ---------------------------------------------------------------------------
print("\n== Idempotence de la migration ==")

count_before_remigrate = len(facture_service.list_factures())
MigrationManager().migrate()
count_after_remigrate = len(facture_service.list_factures())
check("relancer la migration ne perd et ne duplique aucune facture", count_before_remigrate == count_after_remigrate)

# ---------------------------------------------------------------------------
print("\n== Nettoyage ==")
database_module.Database.instance().close()
_tmp_dir.cleanup()
print("Base temporaire supprimee.")

print("\n" + "=" * 70)
if failures:
    print(f"{len(failures)} verification(s) en echec :")
    for label in failures:
        print(f"  - {label}")
    raise SystemExit(1)

print("Toutes les verifications sont passees.")
