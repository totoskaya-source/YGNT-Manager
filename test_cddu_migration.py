"""Test de migration - Sprint 15.0, fondations techniques du module CDDU.

Script autonome (meme convention que test_contract.py/test_facture.py),
execute sur une base SQLite TEMPORAIRE et isolee : la base de donnees reelle
(data/ygnt_manager.db) n'est jamais touchee.

Verifie :
  - les migrations sont additives et idempotentes (executables deux fois) ;
  - les nouvelles colonnes RH existent sur artists/producteurs ;
  - les nouvelles tables contrats_cddu / contrat_cddu_dates /
    contrat_cddu_history existent avec les bonnes colonnes ;
  - le modele/repository/service CDDU fonctionnent de bout en bout
    (numerotation, instantane fige, historique, lignes de dates,
    numero_objet toujours vide).
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import app.database.database as database_module

# Redirige la base AVANT toute instanciation de Database.instance() - la
# vraie base utilisateur (data/ygnt_manager.db) n'est jamais ouverte par ce
# script.
_tmp_dir = tempfile.TemporaryDirectory()
database_module.DB_PATH = Path(_tmp_dir.name) / "test_cddu_migration.db"
database_module.Database._instance = None

from app.database.migrations import MigrationManager  # noqa: E402
from app.models.artist import Artist  # noqa: E402
from app.models.prestation import Prestation  # noqa: E402
from app.models.producteur import Producteur  # noqa: E402
from app.repositories.base_repository import BaseRepository  # noqa: E402
from app.services.artist_service import ArtistService  # noqa: E402
from app.services.contrat_cddu_service import ContratCdduService  # noqa: E402
from app.services.prestation_service import PrestationService  # noqa: E402
from app.services.producteur_service import ProducteurService  # noqa: E402

failures: list[str] = []


def check(label: str, condition: bool) -> None:
    status = "OK" if condition else "ECHEC"
    print(f"[{status}] {label}")
    if not condition:
        failures.append(label)


# ---------------------------------------------------------------------------
print("== Migrations ==")

MigrationManager().migrate()
MigrationManager().migrate()  # idempotence : ne doit jamais lever d'erreur

db = BaseRepository().db


def columns_of(table: str) -> set[str]:
    return {row["name"] for row in db.fetchall(f"PRAGMA table_info({table})")}


check("table contrats_cddu creee", "contrats_cddu" in {
    r["name"] for r in db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
})
check("table contrat_cddu_dates creee", "contrat_cddu_dates" in {
    r["name"] for r in db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
})
check("table contrat_cddu_history creee", "contrat_cddu_history" in {
    r["name"] for r in db.fetchall("SELECT name FROM sqlite_master WHERE type='table'")
})

check("artists.birth_place present", "birth_place" in columns_of("artists"))
check("artists.conges_spectacle_number present", "conges_spectacle_number" in columns_of("artists"))
check("producteurs.convention_collective present", "convention_collective" in columns_of("producteurs"))

cddu_columns = columns_of("contrats_cddu")
for expected in (
    "numero", "prestation_id", "artist_id", "producteur_id",
    "producteur_convention_collective", "artiste_numero_conges_spectacle",
    "artiste_lieu_naissance", "numero_objet", "remuneration_brute",
    "defraiement_deplacement", "defraiement_montant_libre_montant", "status",
):
    check(f"contrats_cddu.{expected} present", expected in cddu_columns)

dates_columns = columns_of("contrat_cddu_dates")
for expected in ("contrat_cddu_id", "prestation_id", "date_travaillee", "nombre_cachets"):
    check(f"contrat_cddu_dates.{expected} present", expected in dates_columns)

check(
    "contrats_cddu.date_debut/date_fin absents (derives, jamais stockes - doc §3)",
    "date_debut" not in cddu_columns and "date_fin" not in cddu_columns,
)

# ---------------------------------------------------------------------------
print("\n== Donnees de test ==")

producteur_service = ProducteurService()
producteur = Producteur(
    nom="YGNT Production",
    forme_juridique="Association loi 1901",
    adresse="28 Rue Joseph Roumanille",
    postal_code="04180",
    city="Villeneuve",
    siret="10572314200011",
    representant="Tanguy Zahn",
    fonction="President",
    convention_collective="Convention collective nationale des entreprises artistiques et culturelles (IDCC 1285)",
)
producteur_id = producteur_service.create_producteur(producteur)
check("producteur cree et actif", producteur_service.get_active_producteur() is not None)

artist_service = ArtistService()
artist = Artist(
    legal_name="Anthony Zahn",
    address="301 Rue du Pigeonnier",
    postal_code="83600",
    city="Frejus",
    birth_date="11/05/1988",
    birth_place="Cavaillon",
    social_number="1 88 05 84 035 041 22",
    conges_spectacle_number="C 381 825",
    instrument="Guitariste",
    qualification="Artiste musicien",
)
artist_id = artist_service.create_artist(artist)
reloaded_artist = artist_service.get_artist(artist_id)
check("artist.birth_place persiste", reloaded_artist.birth_place == "Cavaillon")
check("artist.conges_spectacle_number persiste", reloaded_artist.conges_spectacle_number == "C 381 825")

prestation_service = PrestationService()
prestation_1 = Prestation(nom="Nuits Nomades de Maneo", type_evenement="festival", date_debut="09/07/2026", artist_id=artist_id)
prestation_1_id = prestation_service.create_prestation(prestation_1)
prestation_2 = Prestation(nom="Festival Ete", type_evenement="festival", date_debut="12/07/2026", artist_id=artist_id)
prestation_2_id = prestation_service.create_prestation(prestation_2)

# ---------------------------------------------------------------------------
print("\n== ContratCdduService ==")

cddu_service = ContratCdduService()
prestation_1_reloaded = prestation_service.get_prestation(prestation_1_id)

contrat = cddu_service.build_from_prestation_and_artist(prestation_1_reloaded, artist_id)
check("build_from_prestation_and_artist pre-remplit artiste_nom", contrat.artiste_nom == "Anthony Zahn")
check("build_from_prestation_and_artist pre-remplit artiste_lieu_naissance", contrat.artiste_lieu_naissance == "Cavaillon")
check("build_from_prestation_and_artist pre-remplit artiste_numero_conges_spectacle", contrat.artiste_numero_conges_spectacle == "C 381 825")
check("build_from_prestation_and_artist pre-remplit artiste_fonction depuis instrument", contrat.artiste_fonction == "Guitariste")

contrat.remuneration_brute = "136.37"
contrat.numero_objet = "essai d'injection - doit rester vide"

contrat_id = cddu_service.create_contrat(contrat)
saved = cddu_service.get_contrat(contrat_id)

check("numero attribue au format CDDU-AAAA-XXXX", saved.numero.startswith("CDDU-") and saved.numero.endswith("-0001"))
check("statut par defaut = draft", saved.status == "draft")
check("statut libelle = Brouillon", saved.status_label == "Brouillon")
check("numero_objet reste vide malgre la tentative d'ecriture", saved.numero_objet == "")
check("remuneration_brute convertie en float", saved.remuneration_brute == 136.37)
check("instantane producteur_nom copie", saved.producteur_nom == "YGNT Production")
check("instantane producteur_convention_collective copie", "IDCC 1285" in saved.producteur_convention_collective)
check("instantane artiste_numero_secu copie", saved.artiste_numero_secu == "1 88 05 84 035 041 22")
check("aucun calcul de paie : la valeur saisie est reprise telle quelle", saved.remuneration_brute == 136.37)

second_contrat = cddu_service.build_from_prestation_and_artist(prestation_1_reloaded, artist_id)
second_id = cddu_service.create_contrat(second_contrat)
second_saved = cddu_service.get_contrat(second_id)
check("numerotation independante et sequentielle (2e CDDU = -0002)", second_saved.numero.endswith("-0002"))

history = cddu_service.history(contrat_id)
check("historique de creation enregistre", any(entry["action"] == "Creation" for entry in history))

# ---------------------------------------------------------------------------
print("\n== contrat_cddu_dates ==")

check("aucune ligne de date a la creation (CDDU simple : ajoutee explicitement)", cddu_service.list_dates(contrat_id) == [])

cddu_service.add_date(contrat_id, "09/07/2026", prestation_id=prestation_1_id, nombre_cachets=1)
check("CDDU simple : 1 ligne, 1 cachet, non mensualise", cddu_service.total_cachets(contrat_id) == 1 and not cddu_service.is_mensualise(contrat_id))

date_debut, date_fin = cddu_service.date_range(contrat_id)
check("date_debut/date_fin derivees correctement (une seule date)", date_debut == "09/07/2026" and date_fin == "09/07/2026")

# Mensualisation : memes artiste, deuxieme prestation differente
cddu_service.add_date(contrat_id, "12/07/2026", prestation_id=prestation_2_id, nombre_cachets=1)
check("mensualisation : plusieurs prestations => is_mensualise=True", cddu_service.is_mensualise(contrat_id))
check("nombre total de cachets = somme des lignes (2)", cddu_service.total_cachets(contrat_id) == 2)

date_debut, date_fin = cddu_service.date_range(contrat_id)
check("date_debut/date_fin derivees correctement (deux dates)", date_debut == "09/07/2026" and date_fin == "12/07/2026")

check(
    "CDDU rattache a prestation_2 uniquement via contrat_cddu_dates (many-to-many)",
    contrat_id in [c.id for c in cddu_service.list_for_prestation_via_dates(prestation_2_id)],
)
check(
    "prestation_id du contrat reste la prestation de depart uniquement (informatif)",
    saved.prestation_id == prestation_1_id,
)

history_after_dates = cddu_service.history(contrat_id)
check("historique des ajouts de dates enregistre", sum(1 for e in history_after_dates if e["action"] == "Ajout d'une date") == 2)

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
