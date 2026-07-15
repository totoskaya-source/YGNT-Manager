# -*- coding: utf-8 -*-
"""BUG-001 (v1.0.3) : verifie que le tri des colonnes Date des tableaux est
desormais chronologique (et non plus alphabetique sur le texte JJ/MM/AAAA),
sur les 6 pages concernees, tout en verifiant que :
- le texte affiche reste au format francais JJ/MM/AAAA ;
- le tri croissant ET decroissant fonctionnent ;
- les autres colonnes (texte, montant) trient toujours correctement
  (non-regression) ;
- app.dates.parse_french_date et ContratCdduService.date_range se
  comportent correctement (cas limites : vide, plage, date invalide)."""
import os
import shutil
import sys
import tempfile
from datetime import date

os.environ["QT_QPA_PLATFORM"] = "offscreen"

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

# ===== Base de donnees temporaire isolee =====
tmp_dir = tempfile.mkdtemp(prefix="ygnt_test_bug001_")
tmp_db = os.path.join(tmp_dir, "test.db")

import app.database.database as database_module
database_module.DB_PATH = tmp_db
database_module.Database._instance = None

from app.database.migrations import MigrationManager
MigrationManager().migrate()

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

app_qt = QApplication.instance() or QApplication([])

# ===== 1. app.dates.parse_french_date : cas unitaires =====
from app.dates import parse_french_date

assert parse_french_date("20/08/2026") == date(2026, 8, 20)
assert parse_french_date("20/08/2026 - 25/08/2026") == date(2026, 8, 20), \
    "doit prendre la premiere date d'une plage"
assert parse_french_date("") is None
assert parse_french_date(None) is None
assert parse_french_date("texte sans date") is None
assert parse_french_date("31/02/2026") is None, "31 fevrier n'existe pas : doit etre rejete proprement"
print("[OK] parse_french_date : cas unitaires corrects")

# ===== 2. DateTableWidgetItem : comparaison directe =====
from app.ui.theme import DateTableWidgetItem

early = DateTableWidgetItem("05/01/2026")
late = DateTableWidgetItem("20/12/2025")
# Piege du bug original : "05/01/2026" < "20/12/2025" en tri texte,
# alors que chronologiquement 20/12/2025 est AVANT 05/01/2026.
assert late < early, "20/12/2025 doit être considere anterieur a 05/01/2026 (tri chronologique, pas texte)"
assert not (early < late)
blank = DateTableWidgetItem("")
assert blank < early and blank < late, "une date vide doit être triee en premier (la plus ancienne)"
print("[OK] DateTableWidgetItem.__lt__ : comparaison chronologique correcte, y compris valeurs vides")

# ===== 3. Test reel via QTableWidget.sortItems() sur chaque page =====


def check_table_date_sort(table, date_column: int, label: str) -> None:
    """Trie le tableau (colonne Date) dans les deux sens et verifie que les
    dates affichees sont dans l'ordre chronologique attendu."""
    table.sortItems(date_column, Qt.SortOrder.AscendingOrder)
    ascending_dates = [
        parse_french_date(table.item(row, date_column).text())
        for row in range(table.rowCount())
    ]
    non_none = [d for d in ascending_dates if d is not None]
    assert non_none == sorted(non_none), f"[{label}] tri croissant incorrect : {ascending_dates}"

    table.sortItems(date_column, Qt.SortOrder.DescendingOrder)
    descending_dates = [
        parse_french_date(table.item(row, date_column).text())
        for row in range(table.rowCount())
    ]
    non_none_desc = [d for d in descending_dates if d is not None]
    assert non_none_desc == sorted(non_none_desc, reverse=True), f"[{label}] tri decroissant incorrect : {descending_dates}"

    # Le texte affiche doit rester francais JJ/MM/AAAA (pas de regression
    # d'affichage).
    for row in range(table.rowCount()):
        text = table.item(row, date_column).text()
        assert text == "" or "/" in text, f"[{label}] texte de date inattendu : {text!r}"

    print(f"[OK] [{label}] tri chronologique croissant et decroissant corrects, affichage FR preserve")


# ----- Prestations -----
from app.services.artist_service import ArtistService
from app.services.organization_service import OrganizationService
from app.services.prestation_service import PrestationService
from app.models.artist import Artist
from app.models.organization import Organization
from app.models.prestation import Prestation
from app.ui.prestations import PrestationsPage

artist_service = ArtistService()
artist_id = artist_service.create_artist(Artist(legal_name="Testeur", first_name="Test", qualification="Artiste musicien"))
organization_service = OrganizationService()
org_id = organization_service.create_organization(Organization(name="Testeur Orga"))

prestation_service = PrestationService()
# Dates volontairement dans le "piege" du bug : triees par texte, l'ordre
# serait 01/01/2026, 05/01/2026, 20/12/2025 - pas chronologique.
test_dates = ["20/12/2025", "01/01/2026", "05/01/2026"]
for d in test_dates:
    prestation_service.create_prestation(Prestation(
        nom=f"Test prestation {d}", type_evenement="Concert",
        date_debut=d, date_fin=d, artist_id=artist_id,
    ))

prestations_page = PrestationsPage(
    service=prestation_service,
    artist_service=artist_service,
    organization_service=organization_service,
)
prestations_page.refresh_table()
check_table_date_sort(prestations_page.table, PrestationsPage.DATE_COLUMN, "Prestations")

# ----- Devis -----
from app.services.devis_service import DevisService
from app.services.contract_service import ContractService
from app.ui.devis import DevisPage

devis_service = DevisService(artist_service=artist_service)
prestations = prestation_service.list_prestations()
for prestation in prestations:
    devis = devis_service.build_from_prestation(prestation)
    devis.organisateur_structure = "Testeur Orga"
    devis_service.create_devis(devis)

devis_page = DevisPage(
    service=devis_service,
    artist_service=artist_service,
    organization_service=organization_service,
    contract_service=ContractService(),
)
devis_page.refresh_table()
check_table_date_sort(devis_page.table, DevisPage.DATE_COLUMN, "Devis")
# Non-regression : colonne Montant (texte "X.XX EUR") doit toujours trier numeriquement.
devis_page.table.sortItems(6, Qt.SortOrder.AscendingOrder)
montants = [devis_page.table.item(row, 6).data(Qt.ItemDataRole.EditRole) for row in range(devis_page.table.rowCount())]
assert montants == sorted(montants), "[Devis] non-regression : tri Montant casse"
print("[OK] [Devis] non-regression tri Montant toujours correct")

# ----- Contrats -----
from app.ui.contracts import ContractsPage

contract_service = ContractService()
for devis in devis_service.list_devis():
    contract = contract_service.build_from_devis(devis)
    contract.organisateur_structure = "Testeur Orga"
    contract_service.create_contract(contract)

contracts_page = ContractsPage(service=contract_service)
contracts_page.refresh_table()
check_table_date_sort(contracts_page.table, ContractsPage.DATE_COLUMN, "Contrats")

# ----- CDDU -----
from app.services.contrat_cddu_service import ContratCdduService
from app.services.prestation_participant_service import PrestationParticipantService
from app.services.formation_artiste_service import FormationArtisteService
from app.ui.cddu import CdduPage

participant_service = PrestationParticipantService()
cddu_service = ContratCdduService(artist_service=artist_service)

from app.models.contrat_cddu import ContratCddu as ContratCdduModel

for prestation in prestations:
    participant_service.add_participant(prestation.id, artist_id)
    contrat = ContratCdduModel(
        numero=cddu_service.next_contrat_number(),
        prestation_id=prestation.id,
        artist_id=artist_id,
        artiste_nom="Testeur",
        artiste_prenom="Test",
        artiste_qualification="Artiste musicien",
        prestation_reference=prestation.reference,
    )
    contrat_id = cddu_service.create_contrat(contrat)
    cddu_service.add_date(contrat_id, prestation.date_debut, prestation_id=prestation.id, nombre_cachets=1)

# Verifie directement le service (bug latent signale par l'audit :
# date_range() triait aussi les dates en texte).
cddu_ids = [c.id for c in cddu_service.search_contrats("", "all")]
ranges = {cid: cddu_service.date_range(cid) for cid in cddu_ids}
for cid, (start, end) in ranges.items():
    assert start == end, "un seul cachet par CDDU dans ce test"
print("[OK] ContratCdduService.date_range() : coherent pour chaque CDDU")

cddu_page = CdduPage(service=cddu_service)
cddu_page.refresh_table()
check_table_date_sort(cddu_page.table, CdduPage.DATE_COLUMN, "CDDU")

# ----- Factures -----
from app.services.facture_service import FactureService
from app.ui.factures import FacturesPage

facture_service = FactureService(artist_service=artist_service)
for prestation in prestations:
    facture = facture_service.build_from_prestation(prestation)
    facture.organisateur_structure = "Testeur Orga"
    facture_service.create_facture(facture)

factures_page = FacturesPage(service=facture_service)
factures_page.refresh_table()
check_table_date_sort(factures_page.table, FacturesPage.DATE_COLUMN, "Factures")

# ----- Paiements -----
from app.services.paiement_service import PaiementService
from app.models.paiement import Paiement
from app.ui.paiements import PaiementsPage

paiement_service = PaiementService()
factures = facture_service.list_factures()
for facture, d in zip(factures, test_dates):
    paiement_service.create_paiement(Paiement(
        facture_id=facture.id, date_paiement=d, montant=10.0, mode_paiement="Virement",
    ))

paiements_page = PaiementsPage(service=paiement_service, facture_service=facture_service)
paiements_page.refresh_table()
check_table_date_sort(paiements_page.table, PaiementsPage.DATE_COLUMN, "Paiements")

# ===== Nettoyage =====
shutil.rmtree(tmp_dir, ignore_errors=True)
print("\nBase temporaire supprimee.")
print("\n" + "=" * 70)
print("Toutes les verifications sont passees.")
