# -*- coding: utf-8 -*-
"""BUG-002 (v1.0.3) : verifie qu'aucune double virgule n'apparait plus dans
l'adresse du CDDU genere, y compris dans le cas exact signale (un champ
Adresse saisi avec une virgule de fin), et que le format final reste
inchange quand les donnees sont propres ou qu'un champ est simplement vide."""
import os
import shutil
import sys
import tempfile

os.environ["QT_QPA_PLATFORM"] = "offscreen"

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from app.cddu.generator import CdduGenerator

# ===== 1. Unitaire : _build_adresse_complete =====

build = CdduGenerator._build_adresse_complete

# Cas exact signale (BUG-002) : adresse saisie avec une virgule de fin.
assert build("28 rue Joseph Roumanille 04180 Villa 39,", "04180", "Villeneuve") == \
    "28 rue Joseph Roumanille 04180 Villa 39, 04180 Villeneuve"

# Adresse avec espaces parasites autour de la virgule de fin.
assert build("28 rue Joseph Roumanille ,  ", "04180", "Villeneuve") == \
    "28 rue Joseph Roumanille, 04180 Villeneuve"

# Cas normal (donnees propres) : format inchange.
assert build("28 rue Joseph Roumanille", "04180", "Villeneuve") == \
    "28 rue Joseph Roumanille, 04180 Villeneuve"

# Champ vide (postal_code) : pas de double espace/virgule.
assert build("28 rue Joseph Roumanille", "", "Villeneuve") == \
    "28 rue Joseph Roumanille, Villeneuve"

# Champ vide (city) : pas de virgule finale parasite.
assert build("28 rue Joseph Roumanille", "04180", "") == \
    "28 rue Joseph Roumanille, 04180"

# Adresse vide : seul CP VILLE.
assert build("", "04180", "Villeneuve") == "04180 Villeneuve"

# Tout vide.
assert build("", "", "") == ""

# None au lieu de chaine vide (valeurs venant directement de la DB).
assert build(None, "04180", "Villeneuve") == "04180 Villeneuve"

print("[OK] CdduGenerator._build_adresse_complete : tous les cas unitaires corrects")

# ===== 2. Reel : generation DOCX via le vrai CdduGenerator =====
tmp_dir = tempfile.mkdtemp(prefix="ygnt_test_bug002_")

import app.database.database as database_module
database_module.DB_PATH = os.path.join(tmp_dir, "test.db")
database_module.Database._instance = None

from app.database.migrations import MigrationManager
MigrationManager().migrate()

from app.models.contrat_cddu import ContratCddu
from app.models.contrat_cddu_date import ContratCdduDate
from docx import Document

contrat = ContratCddu(
    numero="CDDU-TEST-BUG002",
    producteur_nom="YGNT Production",
    producteur_adresse="28 rue Joseph Roumanille 04180 Villa 39,",  # virgule de fin (cas signale)
    producteur_postal_code="04180",
    producteur_city="Villeneuve",
    producteur_representant="Tanguy ZAHN",
    producteur_fonction="President",
    artiste_nom="ZAHN",
    artiste_prenom="Anthony",
    artiste_adresse="301 rue du Pigeonnier,",  # meme cas, cote artiste
    artiste_postal_code="83600",
    artiste_city="Frejus",
    artiste_qualification="Artiste musicien",
    artiste_fonction="Guitare",
    prestation_reference="TEST-BUG002",
    prestation_objet="Concert test BUG-002",
)

generator = CdduGenerator(os.path.join(ROOT, "templates", "contrat_cddu.docx"))
output_path = os.path.join(tmp_dir, "test_bug002.docx")
generator.generate(contrat, [ContratCdduDate(date_travaillee="20/08/2026", nombre_cachets=1)], output_path)

doc = Document(output_path)
full_text = "\n".join(p.text for p in doc.paragraphs)

assert ",," not in full_text, f"double virgule encore presente dans le document genere :\n{full_text}"
assert "représentée par Tanguy ZAHN, agissant en qualité de President." in full_text
assert "28 rue Joseph Roumanille 04180 Villa 39, 04180 Villeneuve - FR" in full_text, \
    "adresse producteur incorrecte apres correction"
assert "301 rue du Pigeonnier, 83600 Frejus" in full_text, "adresse artiste incorrecte apres correction"
print("[OK] Document CDDU reel genere : aucune double virgule, format d'adresse inchange")

shutil.rmtree(tmp_dir, ignore_errors=True)
print("\nBase et fichiers temporaires supprimes.")
print("\n" + "=" * 70)
print("Toutes les verifications sont passees.")
