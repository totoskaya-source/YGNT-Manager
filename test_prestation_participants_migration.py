"""Test de migration - Sprint 15.5, Equipe de prestation (prestation_participants).

Script autonome (meme convention que test_cddu_migration.py), execute sur une
base SQLite TEMPORAIRE et isolee : la base de donnees reelle
(data/ygnt_manager.db) n'est jamais touchee.

Verifie :
  - la migration est additive et idempotente ;
  - la table prestation_participants existe avec les bonnes colonnes et
    contraintes (UNIQUE, cascade) ;
  - la relation many-to-many Prestation <-> Artiste fonctionne (plusieurs
    participants par prestation, un artiste dans plusieurs prestations) ;
  - role/ordre sont optionnels ;
  - un doublon (meme prestation + meme artiste) est refuse ;
  - la suppression d'une Prestation ou d'un Artiste supprime la ligne de
    participation (cascade), sans supprimer l'autre entite ;
  - le contrat de cession, le devis et la facture ne sont JAMAIS alimentes
    automatiquement par l'equipe de prestation - regle intangible du
    Sprint 15.5, verifiee au niveau du schema ET au niveau fonctionnel.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import app.database.database as database_module

_tmp_dir = tempfile.TemporaryDirectory()
database_module.DB_PATH = Path(_tmp_dir.name) / "test_prestation_participants.db"
database_module.Database._instance = None

from app.database.migrations import MigrationManager  # noqa: E402
from app.models.artist import Artist  # noqa: E402
from app.models.contract import Contract  # noqa: E402
from app.models.prestation import Prestation  # noqa: E402
from app.repositories.base_repository import BaseRepository  # noqa: E402
from app.services.artist_service import ArtistService  # noqa: E402
from app.services.contract_service import ContractService  # noqa: E402
from app.services.prestation_participant_service import PrestationParticipantService  # noqa: E402
from app.services.prestation_service import PrestationService  # noqa: E402

failures: list[str] = []


def check(label: str, condition: bool) -> None:
    status = "OK" if condition else "ECHEC"
    print(f"[{status}] {label}")
    if not condition:
        failures.append(label)


# ---------------------------------------------------------------------------
print("== Migrations ==")

MigrationManager().migrate()
MigrationManager().migrate()  # idempotence

db = BaseRepository().db


def columns_of(table: str) -> set[str]:
    return {row["name"] for row in db.fetchall(f"PRAGMA table_info({table})")}


tables = {r["name"] for r in db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")}
check("table prestation_participants creee", "prestation_participants" in tables)

pp_columns = columns_of("prestation_participants")
for expected in ("id", "prestation_id", "artiste_id", "role", "ordre", "created_at", "updated_at"):
    check(f"prestation_participants.{expected} present", expected in pp_columns)

# ---------------------------------------------------------------------------
print("\n== Regle intangible : aucune trace de l'equipe dans cession/devis/facture ==")

for table in ("contracts", "devis", "factures"):
    cols = columns_of(table)
    check(
        f"{table} ne porte aucune colonne liee a prestation_participants",
        not any("participant" in c.lower() for c in cols),
    )

# ---------------------------------------------------------------------------
print("\n== Donnees de test ==")

artist_service = ArtistService()
prestation_service = PrestationService()

formation_sanfuego = artist_service.create_artist(Artist(legal_name="Sanfuego", instrument="Groupe", qualification="Artiste musicien"))
anthony_id = artist_service.create_artist(Artist(legal_name="Anthony Zahn", instrument="Guitariste", qualification="Artiste musicien"))
miguel_id = artist_service.create_artist(Artist(legal_name="Miguel", instrument="Batteur", qualification="Artiste musicien"))
carlos_id = artist_service.create_artist(Artist(legal_name="Carlos", instrument="Bassiste", qualification="Artiste musicien"))

prestation_1_id = prestation_service.create_prestation(
    Prestation(nom="Festival Ete", type_evenement="festival", date_debut="09/07/2026", artist_id=formation_sanfuego)
)
prestation_2_id = prestation_service.create_prestation(
    Prestation(nom="Mariage prive", type_evenement="mariage", date_debut="12/07/2026", artist_id=formation_sanfuego)
)

# ---------------------------------------------------------------------------
print("\n== Relation many-to-many ==")

participant_service = PrestationParticipantService()

participant_service.add_participant(prestation_1_id, anthony_id, role="Guitariste", ordre=1)
participant_service.add_participant(prestation_1_id, miguel_id, role="Batteur", ordre=2)
participant_service.add_participant(prestation_1_id, carlos_id)  # role/ordre optionnels

team_1 = participant_service.list_participants(prestation_1_id)
check("prestation 1 a bien 3 participants", len(team_1) == 3)
check("role/ordre optionnels acceptes (Carlos sans role ni ordre)", any(p.artiste_id == carlos_id and p.role == "" and p.ordre is None for p in team_1))
check("l'ordre saisi est respecte", [p.artiste_id for p in team_1[:2]] == [anthony_id, miguel_id])

# Anthony participe aussi a la prestation 2 : un artiste dans plusieurs prestations
participant_service.add_participant(prestation_2_id, anthony_id, role="Guitariste")
prestations_for_anthony = participant_service.list_prestations_for_artiste(anthony_id)
check("un artiste peut participer a plusieurs prestations", len(prestations_for_anthony) == 2)

# Doublon refuse
try:
    participant_service.add_participant(prestation_1_id, anthony_id, role="Guitariste (bis)")
    check("un doublon (meme prestation + meme artiste) est refuse", False)
except ValueError:
    check("un doublon (meme prestation + meme artiste) est refuse", True)

# ---------------------------------------------------------------------------
print("\n== Suppression en cascade ==")

# Suppression d'un artiste : sa ligne de participation disparait, la prestation reste
artist_service.delete_artist(carlos_id)
team_1_after_artist_delete = participant_service.list_participants(prestation_1_id)
check("suppression d'un artiste retire sa ligne de participation (cascade)", len(team_1_after_artist_delete) == 2)
check("la prestation elle-meme n'est pas affectee", prestation_service.get_prestation(prestation_1_id) is not None)

# Suppression d'une prestation : ses lignes de participation disparaissent, les artistes restent
prestation_service.delete_prestation(prestation_2_id)
prestations_for_anthony_after = participant_service.list_prestations_for_artiste(anthony_id)
check(
    "suppression d'une prestation retire ses lignes de participation (cascade)",
    len(prestations_for_anthony_after) == 1,
)
check("l'artiste lui-meme n'est pas affecte", artist_service.get_artist(anthony_id) is not None)

# ---------------------------------------------------------------------------
print("\n== Non-regression fonctionnelle : contrat de cession ==")

pp_count_before = len(db.fetchall("SELECT id FROM prestation_participants"))

contract_service = ContractService()
contract = Contract(
    organisateur_structure="Mairie de Test",
    spectacle_nom="Sanfuego - Festival Ete",
    artist_id=formation_sanfuego,
    prestation_id=prestation_1_id,
)
contract_id = contract_service.create_contract(contract)
saved_contract = contract_service.get_contract(contract_id)

check("le contrat de cession se cree normalement (Formation seule)", saved_contract is not None)
check(
    "le contrat de cession ne reference que la Formation, jamais un participant individuel",
    saved_contract.artist_id == formation_sanfuego,
)

pp_count_after = len(db.fetchall("SELECT id FROM prestation_participants"))
check(
    "la creation d'un contrat de cession n'a ajoute aucune ligne dans prestation_participants",
    pp_count_after == pp_count_before,
)

# ---------------------------------------------------------------------------
print("\n== Nettoyage ==")

database_module.Database.instance().close()
_tmp_dir.cleanup()
print("Base temporaire supprimee.")

print("\n" + "=" * 60)
if failures:
    print(f"{len(failures)} verification(s) en echec :")
    for label in failures:
        print(f"  - {label}")
    raise SystemExit(1)

print("Toutes les verifications sont passees.")
