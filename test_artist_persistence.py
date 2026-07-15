"""Diagnostic BUG CRITIQUE - champs Artiste non sauvegardes.

Verifie chaque maillon de la chaine, un par un, avec inspection SQL brute a
chaque etape : chargement ArtistDialog, lecture des widgets au clic
Enregistrer, construction de l'objet Artist, ArtistService, ArtistRepository
INSERT, ArtistRepository UPDATE, verification SQLite reelle.

Base SQLite TEMPORAIRE et isolee (data/ygnt_manager.db n'est jamais touchee).
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import app.database.database as database_module

_tmp_dir = tempfile.TemporaryDirectory()
database_module.DB_PATH = Path(_tmp_dir.name) / "test_artist_persistence.db"
database_module.Database._instance = None

from PySide6.QtWidgets import QApplication  # noqa: E402

app = QApplication.instance() or QApplication([])

from app.database.migrations import MigrationManager  # noqa: E402
from app.repositories.base_repository import BaseRepository  # noqa: E402
from app.services.artist_service import ArtistService  # noqa: E402
from app.ui.artist_dialog import ArtistDialog  # noqa: E402

failures: list[str] = []


def check(label: str, condition: bool) -> None:
    status = "OK" if condition else "ECHEC"
    print(f"[{status}] {label}")
    if not condition:
        failures.append(label)


MigrationManager().migrate()
db = BaseRepository().db
service = ArtistService()

ALL_FIELDS = {
    "legal_name": "Zahn",
    "first_name": "Anthony",
    "stage_name": "Tony Z",
    "birth_date": "11/05/1988",
    "birth_place": "Cavaillon",
    "social_number": "1 88 05 84 035 041 22",
    "conges_spectacle_number": "C 381 825",
    "address": "301 Rue du Pigeonnier",
    "postal_code": "83600",
    "city": "Fréjus",
    "phone": "0600000000",
    "email": "anthony@example.com",
    "site_internet": "https://sanfuego.example",
    "instrument": "Guitare",
    "secondary_instruments": "Percussions, Chant",
    "style_musical": "Flamenco",
    "logo_path": "C:/logos/sanfuego.png",
    "photo_path": "C:/photos/anthony.jpg",
}


def fill_dialog(dialog: ArtistDialog) -> None:
    """Etape 1+2 : simule la saisie utilisateur dans CHAQUE widget de
    CHAQUE onglet, exactement comme un vrai clic clavier le ferait."""
    for field_name, value in ALL_FIELDS.items():
        widget = getattr(dialog, field_name)
        widget.setText(value)
    dialog.description.setPlainText("Biographie complete.")
    dialog.notes.setPlainText("Note interne complete.")
    dialog.comments.setPlainText("Commentaire complet.")
    status_index = dialog.status.findText("Salarié")
    dialog.status.setCurrentIndex(status_index)
    dialog.qualification.setCurrentText("Artiste musicien")


def check_object(prefix: str, artist) -> None:
    """Etape 3 : verifie que l'objet Artist construit par save() porte bien
    CHAQUE valeur saisie."""
    for field_name, expected in ALL_FIELDS.items():
        actual = getattr(artist, field_name)
        check(f"{prefix} objet Artist.{field_name} == saisie", actual == expected)
    check(f"{prefix} objet Artist.description", artist.description == "Biographie complete.")
    check(f"{prefix} objet Artist.notes", artist.notes == "Note interne complete.")
    check(f"{prefix} objet Artist.comments", artist.comments == "Commentaire complet.")
    check(f"{prefix} objet Artist.status", artist.status == "Salarié")


def check_row(prefix: str, artist_id: int) -> None:
    """Etape 7 : verification SQLite REELLE, requete brute, sans passer par
    le Repository/dataclass - elimine tout biais de reconstruction Python."""
    row = db.fetchone("SELECT * FROM artists WHERE id=?", (artist_id,))
    row_dict = dict(row)
    for field_name, expected in ALL_FIELDS.items():
        actual = row_dict.get(field_name)
        check(f"{prefix} colonne SQL artists.{field_name} == saisie", actual == expected)
    check(f"{prefix} colonne SQL artists.description", row_dict.get("description") == "Biographie complete.")
    check(f"{prefix} colonne SQL artists.notes", row_dict.get("notes") == "Note interne complete.")
    check(f"{prefix} colonne SQL artists.comments", row_dict.get("comments") == "Commentaire complet.")


# ---------------------------------------------------------------------------
print("== CREATION : remplir TOUS les champs, enregistrer, fermer, rouvrir ==")

dialog = ArtistDialog(None)
dialog.show()
fill_dialog(dialog)

# Etape 2+3 : clic sur Enregistrer (lecture des widgets + construction Artist).
dialog.save()
check("dialog.artist construit apres save()", dialog.artist is not None)
check_object("[CREATE, objet construit]", dialog.artist)

# Etape 4 : ArtistService.create_artist()
artist_id = service.create_artist(dialog.artist)
check("create_artist() renvoie un identifiant", isinstance(artist_id, int))

# Etape 7 : SQLite reel, immediatement apres l'INSERT.
check_row("[CREATE, SQL brut apres INSERT]", artist_id)

# "fermer, rouvrir" : nouvelle instance ArtistService/ArtistRepository (simule
# une vraie fermeture/reouverture d'ecran), relecture complete.
reloaded = ArtistService().get_artist(artist_id)
check("l'artiste est relu apres 'fermeture/reouverture'", reloaded is not None)
check_object("[CREATE, apres relecture]", reloaded)

reopened_dialog = ArtistDialog(None, artist=reloaded)
reopened_dialog.show()
for field_name, expected in ALL_FIELDS.items():
    widget = getattr(reopened_dialog, field_name)
    check(f"[CREATE, widget reaffiche] {field_name}", widget.text() == expected)

# ---------------------------------------------------------------------------
print("\n== MODIFICATION d'un artiste existant : nouvelles valeurs sur TOUS les champs ==")

edit_dialog = ArtistDialog(None, artist=reloaded)
edit_dialog.show()

MODIFIED_FIELDS = {key: f"{value} (modifie)" for key, value in ALL_FIELDS.items()}


def fill_dialog_modified(dialog: ArtistDialog) -> None:
    for field_name, value in MODIFIED_FIELDS.items():
        getattr(dialog, field_name).setText(value)


fill_dialog_modified(edit_dialog)
edit_dialog.description.setPlainText("Biographie modifiee.")
edit_dialog.notes.setPlainText("Note modifiee.")
edit_dialog.comments.setPlainText("Commentaire modifie.")

edit_dialog.save()
check("dialog.artist (modification) construit apres save()", edit_dialog.artist is not None)
check("l'id est preserve en modification", edit_dialog.artist.id == artist_id)

for field_name, expected in MODIFIED_FIELDS.items():
    actual = getattr(edit_dialog.artist, field_name)
    check(f"[EDIT, objet construit] Artist.{field_name} == nouvelle saisie", actual == expected)

service.update_artist(edit_dialog.artist)

row_after_update = dict(db.fetchone("SELECT * FROM artists WHERE id=?", (artist_id,)))
for field_name, expected in MODIFIED_FIELDS.items():
    actual = row_after_update.get(field_name)
    check(f"[EDIT, SQL brut apres UPDATE] artists.{field_name} == nouvelle saisie", actual == expected)

reloaded_after_edit = ArtistService().get_artist(artist_id)
for field_name, expected in MODIFIED_FIELDS.items():
    actual = getattr(reloaded_after_edit, field_name)
    check(f"[EDIT, apres relecture] Artist.{field_name} == nouvelle saisie", actual == expected)

reopened_after_edit = ArtistDialog(None, artist=reloaded_after_edit)
reopened_after_edit.show()
for field_name, expected in MODIFIED_FIELDS.items():
    widget = getattr(reopened_after_edit, field_name)
    check(f"[EDIT, widget reaffiche] {field_name}", widget.text() == expected)

# ---------------------------------------------------------------------------
print("\n== REGRESSION : artiste avec colonnes NULL (cause reelle du bug) ==")

# Reproduit exactement le scenario reel : une ligne inseree sans les champs
# optionnels (facebook/instagram/youtube/siren/... restent NULL en SQLite),
# rechargee (NULL -> None en Python), ouverte dans le dialogue puis
# enregistree SANS RIEN MODIFIER. Avant le correctif, ArtistService._validate()
# levait AttributeError: 'NoneType' object has no attribute 'strip'
# des le premier champ optionnel a None (facebook), avant meme d'atteindre
# repository.update() - c'etait la cause reelle, pas un probleme de
# sauvegarde silencieuse.
db.execute(
    "INSERT INTO artists(stage_name, legal_name, instrument, status) VALUES(?, ?, ?, ?)",
    ("NULL TEST", "Artiste avec colonnes NULL", "Guitare", "Intermittent"),
)
null_artist_id = db.fetchone("SELECT id FROM artists WHERE stage_name='NULL TEST'")["id"]

null_artist = ArtistService().get_artist(null_artist_id)
check("l'artiste charge a bien des champs optionnels a None (reproduit l'etat reel)", null_artist.facebook is None)

null_dialog = ArtistDialog(None, artist=null_artist)
null_dialog.show()
check("le dialogue affiche un artiste a champs None sans planter", null_dialog.legal_name.text() == "Artiste avec colonnes NULL")
# Qualification obligatoire (Sprint 20) : selection explicite necessaire pour
# isoler le test de la regression None (facebook/instagram/...) de la regle
# de validation de la qualification, testee separement ailleurs.
null_dialog.qualification.setCurrentText("Artiste musicien")

try:
    null_dialog.save()
    save_crashed = False
except AttributeError as exc:
    save_crashed = True
    print(f"[ECHEC] save() a plante : {exc!r}")

check("save() ne plante plus sur un artiste dont facebook/instagram/... valent None", not save_crashed)
check("dialog.artist construit (facebook encore None a ce stade : normalise plus tard par _validate())", null_dialog.artist is not None and null_dialog.artist.facebook is None)

try:
    ArtistService().update_artist(null_dialog.artist)
    update_crashed = False
except AttributeError as exc:
    update_crashed = True
    print(f"[ECHEC] update_artist() a plante : {exc!r}")

check("ArtistService.update_artist() ne plante plus sur des champs optionnels a None", not update_crashed)

null_row_after = dict(db.fetchone("SELECT * FROM artists WHERE id=?", (null_artist_id,)))
check("apres correction, l'UPDATE atteint bien SQLite (facebook devient '', jamais NULL->crash)", null_row_after.get("facebook") == "")
check("les champs deja renseignes ne sont pas perdus", null_row_after.get("legal_name") == "Artiste avec colonnes NULL")

# Meme reproduction pour la creation directe d'un Artist() dont un champ
# "preserve depuis la source" vaudrait None (chemin siren/siret/.../facebook
# de ArtistDialog.save() quand _source_artist porte deja un None).
from app.models.artist import Artist  # noqa: E402

artist_with_none = Artist(legal_name="Direct None", facebook=None, siren=None, qualification="Artiste musicien")
try:
    ArtistService().create_artist(artist_with_none)
    create_crashed = False
except AttributeError as exc:
    create_crashed = True
    print(f"[ECHEC] create_artist() a plante : {exc!r}")
check("create_artist() tolere egalement un Artist() construit avec des None explicites", not create_crashed)

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
