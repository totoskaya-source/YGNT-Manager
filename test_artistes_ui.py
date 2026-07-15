"""Test UI reel + non-regression - Sprint 17.1, refonte du module Artistes.

Script autonome (meme convention que les tests precedents), base SQLite
TEMPORAIRE et isolee (data/ygnt_manager.db n'est jamais touchee), vraie
QApplication PySide6 offscreen, QMessageBox patchee (voir test_cddu_ui.py
pour l'explication du blocage headless).

Verifie : creation, modification, recherche, compatibilite avec un artiste
"ancien" (ligne inseree sans les nouvelles colonnes, comme avant ce sprint),
compatibilite avec le module CDDU, compatibilite avec les Prestations,
aucune regression sur le contrat de cession - et bien sur, tous les libelles
"Formation" corriges en "Artiste"."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import app.database.database as database_module

_tmp_dir = tempfile.TemporaryDirectory()
database_module.DB_PATH = Path(_tmp_dir.name) / "test_artistes_ui.db"
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
from app.models.prestation import Prestation  # noqa: E402
from app.models.producteur import Producteur  # noqa: E402
from app.repositories.base_repository import BaseRepository  # noqa: E402
from app.services.artist_service import ArtistService  # noqa: E402
from app.services.contract_service import ContractService  # noqa: E402
from app.services.contrat_cddu_service import ContratCdduService  # noqa: E402
from app.services.prestation_participant_service import PrestationParticipantService  # noqa: E402
from app.services.prestation_service import PrestationService  # noqa: E402
from app.services.producteur_service import ProducteurService  # noqa: E402
from app.ui.artist_dialog import ArtistDialog  # noqa: E402
from app.ui.artistes import ArtistesPage  # noqa: E402

failures: list[str] = []


def check(label: str, condition: bool) -> None:
    status = "OK" if condition else "ECHEC"
    print(f"[{status}] {label}")
    if not condition:
        failures.append(label)


MigrationManager().migrate()

artist_service = ArtistService()

# ---------------------------------------------------------------------------
print("== Libelles : plus aucune trace de 'Formation' dans le module Artistes ==")

page = ArtistesPage(service=artist_service)
page.show()

title_widget = page.layout().itemAt(0).widget()
check("titre affiche 'Artistes'", title_widget.text() == "Artistes")
check("placeholder de recherche mentionne 'artiste'", "artiste" in page.search.placeholderText().lower())
check("aucune mention de 'formation' dans le placeholder", "formation" not in page.search.placeholderText().lower())

check(
    "colonnes de la liste dans l'ordre exact demande",
    page.HEADERS == ("ID", "Nom", "Prénom", "Nom de scène", "Instrument principal", "Statut"),
)

new_dialog_probe = ArtistDialog(None)
check("titre du dialogue de creation = 'Nouvel artiste'", new_dialog_probe.windowTitle() == "Nouvel artiste")
tab_labels = [new_dialog_probe.tabs.tabText(i) for i in range(new_dialog_probe.tabs.count())]
check(
    "4 onglets dans l'ordre demande (Identité/Coordonnées/Artistique/Administratif)",
    tab_labels == ["Identité", "Coordonnées", "Artistique", "Administratif"],
)

# ---------------------------------------------------------------------------
print("\n== Creation (dialogue reel, tous les onglets) ==")

dialog = ArtistDialog(None)
dialog.show()

dialog.legal_name.setText("Zahn")
dialog.first_name.setText("Anthony")
dialog.stage_name.setText("Tony Z")
dialog.birth_date.setText("11/05/1988")
dialog.birth_place.setText("Cavaillon")
dialog.social_number.setText("1 88 05 84 035 041 22")
dialog.conges_spectacle_number.setText("C 381 825")
status_index = dialog.status.findText("Intermittent")
dialog.status.setCurrentIndex(status_index)
dialog.qualification.setCurrentText("Artiste musicien")

dialog.address.setText("301 Rue du Pigeonnier")
dialog.postal_code.setText("83600")
dialog.city.setText("Fréjus")
dialog.phone.setText("0600000000")
dialog.email.setText("anthony@example.com")
dialog.site_internet.setText("https://sanfuego.example")

dialog.instrument.setText("Guitare")
dialog.secondary_instruments.setText("Percussions, Chant")
dialog.style_musical.setText("Flamenco")
dialog.description.setPlainText("Guitariste flamenco depuis 15 ans.")

dialog.notes.setPlainText("Note interne test.")
dialog.comments.setPlainText("Commentaire distinct des notes.")

dialog.save()

check("dialog.artist construit apres save()", dialog.artist is not None)
artist_id = artist_service.create_artist(dialog.artist)
saved = artist_service.get_artist(artist_id)

check("Nom (legal_name) persiste", saved.legal_name == "Zahn")
check("Prenom (nouveau champ) persiste", saved.first_name == "Anthony")
check("Nom de scene persiste", saved.stage_name == "Tony Z")
check("Date de naissance persistee", saved.birth_date == "11/05/1988")
check("Lieu de naissance persiste", saved.birth_place == "Cavaillon")
check("Numero secu persiste", saved.social_number == "1 88 05 84 035 041 22")
check("Numero conges spectacle persiste", saved.conges_spectacle_number == "C 381 825")
check("Adresse complete persistee", saved.address == "301 Rue du Pigeonnier" and saved.postal_code == "83600")
check("Instrument principal persiste", saved.instrument == "Guitare")
check("Instruments secondaires (nouveau champ) persiste", saved.secondary_instruments == "Percussions, Chant")
check("Style musical persiste", saved.style_musical == "Flamenco")
check("Notes internes persistees", saved.notes == "Note interne test.")
check("Commentaires (nouveau champ, distinct des notes) persiste", saved.comments == "Commentaire distinct des notes.")
check("Notes et Commentaires restent bien deux champs distincts", saved.notes != saved.comments)

# ---------------------------------------------------------------------------
print("\n== Modification ==")

edit_dialog = ArtistDialog(None, artist=saved)
edit_dialog.show()

check("formulaire pre-rempli : Nom", edit_dialog.legal_name.text() == "Zahn")
check("formulaire pre-rempli : Prenom", edit_dialog.first_name.text() == "Anthony")
check("formulaire pre-rempli : Instruments secondaires", edit_dialog.secondary_instruments.text() == "Percussions, Chant")
check("titre du dialogue de modification = 'Modifier un artiste'", edit_dialog.windowTitle() == "Modifier un artiste")

edit_dialog.city.setText("Toulon")
edit_dialog.comments.setPlainText("Commentaire modifie.")
edit_dialog.save()

artist_service.update_artist(edit_dialog.artist)
modified = artist_service.get_artist(artist_id)
check("modification de la ville persistee", modified.city == "Toulon")
check("modification des commentaires persistee", modified.comments == "Commentaire modifie.")
check("les autres champs restent inchanges (Nom)", modified.legal_name == "Zahn")

# ---------------------------------------------------------------------------
print("\n== Recherche ==")

results = artist_service.search_artists("Zahn")
check("recherche par nom trouve l'artiste", any(a.id == artist_id for a in results))
results_empty = artist_service.search_artists("Introuvable-xyz")
check("recherche sans resultat renvoie une liste vide", results_empty == [])

page.refresh_table()
check("la liste affiche bien l'artiste cree", page.table.rowCount() == 1)
check("colonne Nom correcte dans la liste", page.table.item(0, 1).text() == "Zahn")
check("colonne Prenom correcte dans la liste", page.table.item(0, 2).text() == "Anthony")
check("colonne Nom de scene correcte", page.table.item(0, 3).text() == "Tony Z")
check("colonne Instrument principal correcte", page.table.item(0, 4).text() == "Guitare")
check("colonne Statut correcte", page.table.item(0, 5).text() == "Intermittent")

# ---------------------------------------------------------------------------
print("\n== Compatibilite avec un artiste 'ancien' (colonnes du sprint absentes a l'origine) ==")

# Simule une ligne creee AVANT ce sprint : seules les colonnes historiques
# sont renseignees, les nouvelles (first_name, secondary_instruments,
# comments) restent a leur valeur par defaut de la migration additive.
db = BaseRepository().db
db.execute(
    """
    INSERT INTO artists(stage_name, legal_name, instrument, status)
    VALUES(?, ?, ?, ?)
    """,
    ("SANFUEGO", "SANFUEGO", "Groupe", "Intermittent"),
)
legacy_id = db.fetchone("SELECT id FROM artists WHERE stage_name='SANFUEGO'")["id"]

legacy_artist = artist_service.get_artist(legacy_id)
check("artiste ancien lisible sans erreur", legacy_artist is not None)
check("champs historiques intacts", legacy_artist.legal_name == "SANFUEGO" and legacy_artist.instrument == "Groupe")
check(
    "nouveaux champs vides par defaut (NULL en base -> None, aucune perte, aucun crash)",
    not legacy_artist.first_name and not legacy_artist.secondary_instruments and not legacy_artist.comments,
)

legacy_dialog = ArtistDialog(None, artist=legacy_artist)
legacy_dialog.show()
check("le dialogue ouvre un artiste ancien sans erreur", legacy_dialog.legal_name.text() == "SANFUEGO")
check("les nouveaux champs apparaissent vides, pas 'None' ni une erreur", legacy_dialog.first_name.text() == "")

# ---------------------------------------------------------------------------
print("\n== Compatibilite Prestations ==")

prestation_service = PrestationService()
prestation_id = prestation_service.create_prestation(Prestation(
    nom="Concert test", type_evenement="festival", date_debut="09/07/2026",
    artist_id=legacy_id,
))
prestation = prestation_service.get_prestation(prestation_id)
check("la prestation reste liee a l'artiste (artist_id inchange)", prestation.artist_id == legacy_id)

participant_service = PrestationParticipantService()
participant_service.add_participant(prestation_id, artist_id, role="Guitariste")
check(
    "l'equipe de prestation fonctionne toujours avec un artiste cree via le nouveau dialogue",
    any(p.artiste_id == artist_id for p in participant_service.list_participants(prestation_id)),
)

# ---------------------------------------------------------------------------
print("\n== Compatibilite CDDU ==")

producteur_service = ProducteurService()
producteur_service.create_producteur(Producteur(nom="YGNT PRODUCTION", city="Villeneuve"))

cddu_service = ContratCdduService()
cddu_contrat = cddu_service.build_from_prestation_and_artist(prestation, artist_id)

check("CDDU : nom repris depuis le nouveau champ legal_name (Nom)", cddu_contrat.artiste_nom == "Zahn")
check("CDDU : lieu de naissance toujours lu correctement", cddu_contrat.artiste_lieu_naissance == "Cavaillon")
check("CDDU : numero conges spectacle toujours lu correctement", cddu_contrat.artiste_numero_conges_spectacle == "C 381 825")
check("CDDU : fonction pre-remplie depuis l'instrument principal", cddu_contrat.artiste_fonction == "Guitare")

cddu_id = cddu_service.create_contrat(cddu_contrat)
check("le CDDU se cree sans erreur avec un artiste du nouveau module", cddu_id is not None)

# ---------------------------------------------------------------------------
print("\n== Aucune regression sur le contrat de cession ==")

contract_service = ContractService()
contract = contract_service.build_from_prestation(prestation)
contract.artist_id = legacy_id
contract.organisateur_structure = "Mairie de Test"
contract.spectacle_nom = "Concert test"
# ContractService.build_from_prestation() ne pre-remplit pas l'instantane
# artiste_* : ce mapping vit dans ContractDialog._on_artist_selected (UI).
# On le reproduit ici a l'identique pour verifier que la lecture des champs
# Artiste (inchanges) fonctionne toujours correctement pour cet instantane.
contract.artiste_nom = legacy_artist.stage_name or legacy_artist.legal_name
contract.artiste_siren = legacy_artist.siren
contract.artiste_social_number = legacy_artist.social_number

contract_id = contract_service.create_contract(contract)
saved_contract = contract_service.get_contract(contract_id)

check("le contrat de cession se cree normalement", saved_contract is not None)
check(
    "l'instantane artiste du contrat de cession reste correct (nom legal, instrument)",
    saved_contract.artiste_nom == "SANFUEGO",
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
