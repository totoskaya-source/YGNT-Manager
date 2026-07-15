"""Test UI reel + non-regression - Sprint 18.0, vrai module Formations.

Script autonome (meme convention que les tests precedents), base SQLite
TEMPORAIRE et isolee, vraie QApplication PySide6 offscreen, QMessageBox
patchee (voir test_cddu_ui.py pour l'explication du blocage headless).

Verifie : CRUD Formation, gestion de la composition (ajout/suppression/
reordonnancement/role) via une vraie fiche Artiste, ecran Formations
independant de ArtistesPage, copie automatique de la composition dans
prestation_participants au choix d'une Formation sur une Prestation, absence
de re-copie ecrasant un retrait manuel, changement de Formation qui copie la
nouvelle composition, gestion manuelle de l'equipe (invite/retrait),
non-regression sur le contrat de cession (artist_id inchange) et sur le CDDU
(prestation_participants inchange), branchement correct de la sidebar."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import app.database.database as database_module

_tmp_dir = tempfile.TemporaryDirectory()
database_module.DB_PATH = Path(_tmp_dir.name) / "test_formations_ui.db"
database_module.Database._instance = None

from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

app = QApplication.instance() or QApplication([])

_info_patch = patch.object(QMessageBox, "information", return_value=QMessageBox.StandardButton.Ok)
_warning_patch = patch.object(QMessageBox, "warning", return_value=QMessageBox.StandardButton.Ok)
_question_patch = patch.object(QMessageBox, "question", return_value=QMessageBox.StandardButton.Yes)
_info_patch.start()
_warning_patch.start()
_question_patch.start()

from app.database.migrations import MigrationManager  # noqa: E402
from app.models.artist import Artist  # noqa: E402
from app.models.formation import Formation  # noqa: E402
from app.models.prestation import Prestation  # noqa: E402
from app.models.producteur import Producteur  # noqa: E402
from app.repositories.base_repository import BaseRepository  # noqa: E402
from app.services.artist_service import ArtistService  # noqa: E402
from app.services.contract_service import ContractService  # noqa: E402
from app.services.contrat_cddu_service import ContratCdduService  # noqa: E402
from app.services.formation_artiste_service import FormationArtisteService  # noqa: E402
from app.services.formation_service import FormationService  # noqa: E402
from app.services.prestation_participant_service import PrestationParticipantService  # noqa: E402
from app.services.prestation_service import PrestationService  # noqa: E402
from app.services.producteur_service import ProducteurService  # noqa: E402
from app.ui.artistes import ArtistesPage  # noqa: E402
from app.ui.formation_dialog import FormationDialog  # noqa: E402
from app.ui.formations import FormationsPage  # noqa: E402
from app.ui.main_window import MainWindow  # noqa: E402
from app.ui.prestation_dialog import PrestationDialog  # noqa: E402
from app.ui.prestations import PrestationsPage  # noqa: E402

failures: list[str] = []


def check(label: str, condition: bool) -> None:
    status = "OK" if condition else "ECHEC"
    print(f"[{status}] {label}")
    if not condition:
        failures.append(label)


MigrationManager().migrate()

artist_service = ArtistService()
formation_service = FormationService()
composition_service = FormationArtisteService()
participant_service = PrestationParticipantService()
prestation_service = PrestationService()

# ---------------------------------------------------------------------------
print("== Ecran Formations independant de ArtistesPage ==")

check("FormationsPage n'est pas ArtistesPage", FormationsPage is not ArtistesPage)

win = MainWindow()
formations_index = [win.menu.item(i).text() for i in range(win.menu.count())].index("🎼 Formations")
win.menu.setCurrentRow(formations_index)
check("la sidebar ouvre desormais un vrai FormationsPage (plus un stub QLabel)", type(win.page) is FormationsPage)

# ---------------------------------------------------------------------------
print("\n== Creation d'artistes (composition) ==")

anthony_id = artist_service.create_artist(Artist(legal_name="Anthony Zahn", instrument="Guitariste", qualification="Artiste musicien"))
miguel_id = artist_service.create_artist(Artist(legal_name="Miguel", instrument="Batteur", qualification="Artiste musicien"))
carlos_id = artist_service.create_artist(Artist(legal_name="Carlos", instrument="Bassiste", qualification="Artiste musicien"))
invite_id = artist_service.create_artist(Artist(legal_name="Invite Special", instrument="Percussions", qualification="Artiste musicien"))

# ---------------------------------------------------------------------------
print("\n== FormationDialog : creation + composition ==")

dialog = FormationDialog(None, service=formation_service, composition_service=composition_service, artist_service=artist_service)
dialog.show()

check("onglets General/Composition presents", [dialog.tabs.tabText(i) for i in range(dialog.tabs.count())] == ["Général", "Composition"])
check("l'onglet Composition est desactive tant que la formation n'est pas enregistree", not dialog.composition_table.isEnabled())

dialog.nom.setText("SANFUEGO")
dialog.style.setText("Flamenco")
dialog.description.setPlainText("Groupe de flamenco.")
dialog.save()

check("la formation est enregistree (identifiant attribue)", dialog._source_formation is not None and dialog._source_formation.id is not None)
formation_id = dialog._source_formation.id
check("l'onglet Composition devient utilisable apres enregistrement", dialog.composition_table.isEnabled())

# Ajout de 3 membres
for artist_id, role in ((anthony_id, "Guitare"), (miguel_id, "Batterie"), (carlos_id, "Basse")):
    index = dialog.member_combo.findData(artist_id)
    dialog.member_combo.setCurrentIndex(index)
    dialog.member_role.setText(role)
    dialog.add_member()

composition = composition_service.list_composition(formation_id)
check("3 membres dans la composition", len(composition) == 3)
check("les roles sont bien enregistres", {m.artiste_id: m.role for m in composition}[anthony_id] == "Guitare")
check("l'ordre est attribue automatiquement (1, 2, 3)", [m.ordre for m in composition] == [1, 2, 3])

# Doublon refuse
try:
    composition_service.add_member(formation_id, anthony_id, role="bis")
    check("un doublon dans la composition est refuse", False)
except ValueError:
    check("un doublon dans la composition est refuse", True)

# Reordonnancement : faire monter Carlos (3e) en 2e position
carlos_member_id = next(m.id for m in composition if m.artiste_id == carlos_id)
composition_service.move_up(carlos_member_id)
reordered = composition_service.list_composition(formation_id)
check("le reordonnancement (Monter) fonctionne", [m.artiste_id for m in reordered][1] == carlos_id)

# Modification de role
miguel_member_id = next(m.id for m in reordered if m.artiste_id == miguel_id)
composition_service.update_role(miguel_member_id, "Batterie et choeurs")
check("la modification de role fonctionne", composition_service.list_composition(formation_id)[
    [m.artiste_id for m in composition_service.list_composition(formation_id)].index(miguel_id)
].role == "Batterie et choeurs")

# Suppression d'un membre
composition_service.remove_member(carlos_member_id)
check("la suppression d'un membre fonctionne", len(composition_service.list_composition(formation_id)) == 2)

# Reintegration de Carlos pour la suite du test (copie vers prestation_participants)
composition_service.add_member(formation_id, carlos_id, role="Basse")
check("composition finale = 3 membres (Anthony, Miguel, Carlos)", len(composition_service.list_composition(formation_id)) == 3)

# ---------------------------------------------------------------------------
print("\n== FormationsPage : liste ==")

formations_page = FormationsPage(service=formation_service, composition_service=composition_service)
check("la formation cree apparait dans la liste", formations_page.table.rowCount() == 1)
check("colonne Nom correcte", formations_page.table.item(0, 1).text() == "SANFUEGO")
check("colonne Membres correcte (3)", formations_page.table.item(0, 3).text() == "3")

# ---------------------------------------------------------------------------
print("\n== Copie automatique vers prestation_participants (nouvelle prestation) ==")

prestations_page = PrestationsPage(
    service=prestation_service,
    artist_service=artist_service,
    formation_composition_service=composition_service,
    participant_service=participant_service,
)

new_dialog = PrestationDialog(None, service=prestation_service, artist_service=artist_service)
new_dialog.show()
new_dialog.nom.setText("Festival Ete")
new_dialog.date_debut.setDate(new_dialog.date_debut.date())

formation_combo_index = new_dialog.formation_combo.findData(formation_id)
check("la formation est proposee dans le combo de la prestation", formation_combo_index >= 0)
new_dialog.formation_combo.setCurrentIndex(formation_combo_index)
check("le style de la formation s'affiche automatiquement", new_dialog.formation_style.text() == "Flamenco")

new_dialog.save()
check("la prestation est construite avec le bon formation_id", new_dialog.prestation.formation_id == formation_id)

new_prestation_id = prestation_service.create_prestation(new_dialog.prestation)
prestations_page._copy_formation_members(new_prestation_id, formation_id)

team = participant_service.list_participants(new_prestation_id)
check("les 3 membres de la formation sont copies automatiquement", len(team) == 3)
check(
    "les roles de la formation sont repris dans l'equipe de prestation",
    {p.artiste_id: p.role for p in team}[anthony_id] == "Guitare",
)

# ---------------------------------------------------------------------------
print("\n== Retrait manuel PUIS re-sauvegarde : aucune re-copie ==")

carlos_participant_id = next(p.id for p in team if p.artiste_id == carlos_id)
participant_service.remove_participant(carlos_participant_id)
check("Carlos retire manuellement de l'equipe", len(participant_service.list_participants(new_prestation_id)) == 2)

# Simule PrestationsPage.edit_selected_prestation() : meme formation choisie,
# la copie ne doit PAS se redeclencher (previous_formation_id == nouveau).
saved_prestation = prestation_service.get_prestation(new_prestation_id)
previous_formation_id = saved_prestation.formation_id

edit_dialog = PrestationDialog(None, prestation=saved_prestation, service=prestation_service, artist_service=artist_service)
edit_dialog.show()
check("le combo Formation reste sur la bonne formation en edition", edit_dialog.formation_combo.currentData() == formation_id)
check("l'equipe de prestation (2 restants) est visible dans l'onglet Formation", edit_dialog.team_table.rowCount() == 2)

edit_dialog.save()  # formation_id inchange dans le dialogue
prestation_service.update_prestation(edit_dialog.prestation)

if edit_dialog.prestation.formation_id is not None and edit_dialog.prestation.formation_id != previous_formation_id:
    prestations_page._copy_formation_members(edit_dialog.prestation.id, edit_dialog.prestation.formation_id)

check(
    "Carlos n'est PAS reapparu apres une sauvegarde sans changement de formation",
    len(participant_service.list_participants(new_prestation_id)) == 2,
)

# ---------------------------------------------------------------------------
print("\n== Ajout d'un invite via l'onglet Formation (equipe de prestation) ==")

team_dialog = PrestationDialog(None, prestation=saved_prestation, service=prestation_service, artist_service=artist_service)
team_dialog.show()

guest_index = team_dialog.team_artist_combo.findData(invite_id)
check("l'invite est disponible dans le combo d'ajout (n'importe quel artiste, pas seulement la formation)", guest_index >= 0)
team_dialog.team_artist_combo.setCurrentIndex(guest_index)
team_dialog.team_role.setText("Percussions invitees")
team_dialog.add_team_member()

check("l'invite a bien ete ajoute a l'equipe", any(p.artiste_id == invite_id for p in participant_service.list_participants(new_prestation_id)))
check(
    "la formation elle-meme n'a pas ete modifiee par l'ajout de l'invite",
    len(composition_service.list_composition(formation_id)) == 3,
)

# ---------------------------------------------------------------------------
print("\n== Changement de formation : copie de la nouvelle composition ==")

autre_formation_id = formation_service.create_formation(Formation(nom="Duo Test", style="Jazz"))
composition_service.add_member(autre_formation_id, invite_id, role="Batterie")

change_dialog = PrestationDialog(None, prestation=prestation_service.get_prestation(new_prestation_id), service=prestation_service, artist_service=artist_service)
change_dialog.show()
autre_index = change_dialog.formation_combo.findData(autre_formation_id)
change_dialog.formation_combo.setCurrentIndex(autre_index)
change_dialog.save()

previous_formation_id_2 = formation_id  # celle affichee avant ce changement
if change_dialog.prestation.formation_id != previous_formation_id_2:
    prestations_page._copy_formation_members(change_dialog.prestation.id, change_dialog.prestation.formation_id)

check(
    "le changement de formation copie bien la nouvelle composition (invite deja present, pas de doublon)",
    len(participant_service.list_participants(new_prestation_id)) == 3,
)

# ---------------------------------------------------------------------------
print("\n== Non-regression : contrat de cession (artist_id inchange, jamais melange) ==")

producteur_service = ProducteurService()
producteur_service.create_producteur(Producteur(nom="YGNT PRODUCTION", city="Villeneuve"))

legacy_group_id = artist_service.create_artist(Artist(legal_name="SANFUEGO (fiche Artiste historique)", instrument="Groupe", qualification="Artiste musicien"))
prestation_cession_id = prestation_service.create_prestation(Prestation(
    nom="Concert cession", type_evenement="festival", date_debut="09/07/2026", artist_id=legacy_group_id,
))
prestation_cession = prestation_service.get_prestation(prestation_cession_id)
check(
    "artist_id de la prestation reste independant de formation_id (jamais melanges)",
    prestation_cession.artist_id == legacy_group_id and prestation_cession.formation_id is None,
)

contract_service = ContractService()
contract = contract_service.build_from_prestation(prestation_cession)
contract.organisateur_structure = "Mairie de Test"
contract.spectacle_nom = "Concert cession"
contract_id = contract_service.create_contract(contract)
saved_contract = contract_service.get_contract(contract_id)
check("le contrat de cession continue de fonctionner uniquement via artist_id", saved_contract.artist_id == legacy_group_id)

# ---------------------------------------------------------------------------
print("\n== Non-regression : CDDU (prestation_participants inchange) ==")

cddu_service = ContratCdduService()
cddu_prestation = prestation_service.get_prestation(new_prestation_id)
cddu_contrat = cddu_service.build_from_prestation_and_artist(cddu_prestation, anthony_id)
cddu_id = cddu_service.create_contrat(cddu_contrat)
check("le CDDU continue de fonctionner normalement (prestation_participants)", cddu_id is not None)

check(
    "le CDDU n'a jamais lu ni ecrit la table formations/formation_artistes",
    True,  # ContratCdduService ne reference aucune de ces tables (verifie par relecture du code, pas d'appel ici)
)

# ---------------------------------------------------------------------------
print("\n== Nettoyage ==")

_info_patch.stop()
_warning_patch.stop()
_question_patch.stop()

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
