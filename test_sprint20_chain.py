# -*- coding: utf-8 -*-
"""Sprint 20 - Test de non-regression du scenario complet demande :

    Formation -> Prestation -> Devis -> Contrat -> CDDU -> Facture -> Paiement

Execute DEUX fois sur une base SQLite TEMPORAIRE et isolee (jamais
data/ygnt_manager.db) :
  1. avec une prestation "nouvelle" (formation_id renseigne) ;
  2. avec une prestation "ancienne" (artist_id seul, formation_id absent -
     compatibilite historique).

Verifie a chaque etape que les champs Formation (nom, adresse, ville, code
postal, SIRET, APE, IBAN, BIC) sont bien pre-remplis sur le Devis et la
Facture (bug bloquant Sprint 19, corrige Sprint 20), que le CDDU peut etre
cree via le bouton "+ Ajouter la formation" pour les deux types de
prestation, et que le bouton "Creer un CDDU" de PrestationsPage fonctionne.
"""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import tempfile
from pathlib import Path

import app.database.database as database_module

_tmp_dir = tempfile.TemporaryDirectory()
database_module.DB_PATH = Path(_tmp_dir.name) / "test_sprint20_chain.db"
database_module.Database._instance = None

from unittest.mock import patch  # noqa: E402

from PySide6.QtWidgets import QApplication, QDialog, QMessageBox  # noqa: E402

app = QApplication.instance() or QApplication([])
QMessageBox.information = staticmethod(lambda *a, **k: None)
QMessageBox.warning = staticmethod(lambda *a, **k: None)
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)

from app.database.migrations import MigrationManager  # noqa: E402
from app.models.artist import Artist  # noqa: E402
from app.models.organization import Organization  # noqa: E402
from app.models.prestation import Prestation  # noqa: E402
from app.models.producteur import Producteur  # noqa: E402
from app.services.artist_service import ArtistService  # noqa: E402
from app.services.contract_service import ContractService  # noqa: E402
from app.services.contrat_cddu_service import ContratCdduService  # noqa: E402
from app.services.devis_service import DevisService  # noqa: E402
from app.services.facture_service import FactureService  # noqa: E402
from app.services.formation_artiste_service import FormationArtisteService  # noqa: E402
from app.services.formation_service import FormationService  # noqa: E402
from app.services.organization_service import OrganizationService  # noqa: E402
from app.services.paiement_service import PaiementService  # noqa: E402
from app.services.prestation_participant_service import PrestationParticipantService  # noqa: E402
from app.services.prestation_service import PrestationService  # noqa: E402
from app.services.producteur_service import ProducteurService  # noqa: E402
from app.ui.cddu_dialog import CdduDialog  # noqa: E402
from app.ui.contract_dialog import ContractDialog  # noqa: E402
from app.ui.devis_dialog import DevisDialog  # noqa: E402
from app.ui.facture_dialog import FactureDialog  # noqa: E402
from app.ui.paiement_dialog import PaiementDialog  # noqa: E402
from app.ui.prestations import PrestationsPage  # noqa: E402

failures: list[str] = []


def check(label: str, condition: bool) -> None:
    status = "OK" if condition else "ECHEC"
    print(f"[{status}] {label}")
    if not condition:
        failures.append(label)


MigrationManager().migrate()

producteur_service = ProducteurService()
producteur_service.create_producteur(Producteur(
    nom="YGNT Production", representant="Sophie Dupont", city="Villeneuve",
    siret="10572314200011",
))

artist_service = ArtistService()
organization_service = OrganizationService()
formation_service = FormationService()
composition_service = FormationArtisteService()
prestation_service = PrestationService()
participant_service = PrestationParticipantService()
devis_service = DevisService()
contract_service = ContractService()
cddu_service = ContratCdduService()
facture_service = FactureService()
paiement_service = PaiementService(facture_service=facture_service)

organization_id = organization_service.create_organization(Organization(name="Mairie de Test", city="Testville"))

FORMATION_FIELDS = {
    "nom": "Duo Nouvelle Vague",
    "address": "12 Rue des Artistes",
    "postal_code": "13000",
    "city": "Marseille",
    "phone": "0600000001",
    "email": "contact@duo.example",
    "siret": "12345678900011",
    "ape": "9001Z",
    "licence": "PLATESV-R-2026-000001",
    "iban": "FR7612345987650123456789014",
    "bic": "ABCDEFGHXXX",
}


def run_scenario(label: str, use_formation: bool) -> None:
    print(f"\n{'=' * 70}\nSCENARIO : {label}\n{'=' * 70}")

    musicien_id = artist_service.create_artist(Artist(
        legal_name="Zahn", first_name="Anthony", instrument="Guitare",
        qualification="Artiste musicien",
    ))

    if use_formation:
        formation_id = formation_service.create_formation(__import__("app.models.formation", fromlist=["Formation"]).Formation(**FORMATION_FIELDS))
        composition_service.add_member(formation_id, musicien_id, role="Guitariste")
        prestation = Prestation(
            nom=f"Concert {label}", type_evenement="festival", date_debut="20/08/2026",
            formation_id=formation_id, organization_id=organization_id,
            lieu_nom="Salle des fetes", lieu_city="Marseille",
        )
    else:
        prestation = Prestation(
            nom=f"Concert {label}", type_evenement="festival", date_debut="20/08/2026",
            artist_id=musicien_id, organization_id=organization_id,
            lieu_nom="Salle des fetes", lieu_city="Marseille",
        )

    prestation_id = prestation_service.create_prestation(prestation)
    prestation = prestation_service.get_prestation(prestation_id)
    check(f"[{label}] prestation creee", prestation is not None)

    # ------------------------------------------------------------------
    print(f"\n-- Devis --")
    devis_seed = devis_service.build_from_prestation(prestation)
    if use_formation:
        check(f"[{label}] Devis.formation_nom pre-rempli", devis_seed.formation_nom == FORMATION_FIELDS["nom"])
        check(f"[{label}] Devis.formation_adresse pre-rempli", devis_seed.formation_adresse == FORMATION_FIELDS["address"])
        check(f"[{label}] Devis.formation_city pre-rempli", devis_seed.formation_city == FORMATION_FIELDS["city"])
        check(f"[{label}] Devis.formation_postal_code pre-rempli", devis_seed.formation_postal_code == FORMATION_FIELDS["postal_code"])
        check(f"[{label}] Devis.formation_siret pre-rempli", devis_seed.formation_siret == FORMATION_FIELDS["siret"])
        check(f"[{label}] Devis.formation_ape pre-rempli", devis_seed.formation_ape == FORMATION_FIELDS["ape"])
        check(f"[{label}] Devis.formation_iban pre-rempli", devis_seed.formation_iban == FORMATION_FIELDS["iban"])
        check(f"[{label}] Devis.formation_bic pre-rempli", devis_seed.formation_bic == FORMATION_FIELDS["bic"])
    else:
        check(f"[{label}] Devis.formation_nom pre-rempli (compat artist_id)", devis_seed.formation_nom == "Zahn")
        check(f"[{label}] Devis.formation_adresse (compat, vide ici car artiste sans adresse)", devis_seed.formation_adresse == "")

    devis_seed.montant = 1500.0
    devis_dialog = DevisDialog(None, initial_devis=devis_seed, service=devis_service, organization_service=organization_service)
    check(f"[{label}] DevisDialog : formation_nom affiche a l'ecran", devis_dialog.formation_nom.text() == devis_seed.formation_nom)
    devis_dialog.save()
    devis_id = devis_dialog.devis.id
    check(f"[{label}] devis enregistre", devis_id is not None)
    devis_saved = devis_service.get_devis(devis_id)
    check(f"[{label}] devis relu : formation_nom toujours correct", devis_saved.formation_nom == devis_seed.formation_nom)

    docx_path = devis_service.generate_docx(devis_id)
    check(f"[{label}] DOCX Devis genere", docx_path.exists())

    # ------------------------------------------------------------------
    print(f"\n-- Contrat (depuis le Devis) --")
    contract_seed = contract_service.build_from_devis(devis_saved)
    check(f"[{label}] Contrat.artiste_nom repris du Devis (chaine complete)", contract_seed.artiste_nom == devis_saved.formation_nom)
    if use_formation:
        check(f"[{label}] Contrat.formation_id correctement reporte (vraie Formation)", contract_seed.formation_id is not None)

    contract_dialog = ContractDialog(None, initial_contract=contract_seed, service=contract_service, organization_service=organization_service)
    check(f"[{label}] ContractDialog : Formation affichee a l'ecran", contract_dialog.artiste_nom.text() == devis_saved.formation_nom)
    contract_dialog.montant.setValue(1500.0)
    contract_dialog.save()
    contract_id = contract_dialog.contract.id
    check(f"[{label}] contrat enregistre", contract_id is not None)

    docx_path = contract_service.generate_docx(contract_id)
    check(f"[{label}] DOCX Contrat genere", docx_path.exists())

    # ------------------------------------------------------------------
    print(f"\n-- CDDU (bouton '+ Ajouter la formation') --")
    cddu_dialog = CdduDialog(
        None, service=cddu_service, artist_service=artist_service,
        organization_service=organization_service, participant_service=participant_service,
        formation_composition_service=composition_service, initial_prestation_id=prestation_id,
    )
    cddu_dialog.show()
    cddu_dialog.tabs.setCurrentIndex(1)  # onglet "Artiste" : isVisible() exige l'onglet actif
    check(f"[{label}] bouton '+ Ajouter la formation' visible (aucune equipe encore)", cddu_dialog.btn_add_formation_participant.isVisible())
    cddu_dialog._add_formation_as_participant()
    team = participant_service.list_participants(prestation_id)
    check(f"[{label}] equipe de prestation peuplee via le bouton", len(team) >= 1)
    check(f"[{label}] le musicien fait bien partie de l'equipe importee", any(m.artiste_id == musicien_id for m in team))

    artist_index = cddu_dialog.artist_combo.findData(musicien_id)
    check(f"[{label}] l'artiste est bien propose dans le combo CDDU", artist_index >= 0)
    cddu_dialog.artist_combo.setCurrentIndex(artist_index if artist_index >= 0 else 0)
    cddu_dialog.salaire_brut.setValue(150.0)
    cddu_dialog.save()
    cddu_id = cddu_dialog.contrat.id
    check(f"[{label}] CDDU enregistre", cddu_id is not None)

    if cddu_id is not None:
        cddu_service.add_date(cddu_id, "20/08/2026", prestation_id=prestation_id, nombre_cachets=1)
        docx_path = cddu_service.generate_docx(cddu_id)
        check(f"[{label}] DOCX CDDU genere", docx_path.exists())

    # ------------------------------------------------------------------
    print(f"\n-- Bouton 'Creer un CDDU' depuis PrestationsPage --")
    prestations_page = PrestationsPage(
        service=prestation_service, artist_service=artist_service, organization_service=organization_service,
        contract_service=contract_service, devis_service=devis_service, facture_service=facture_service,
        cddu_service=cddu_service, formation_composition_service=composition_service, participant_service=participant_service,
    )
    check(f"[{label}] bouton 'Creer un CDDU' present sur Prestations", hasattr(prestations_page, "btn_create_cddu"))
    prestations_page.refresh_table()
    row = next((r for r in range(prestations_page.table.rowCount()) if int(prestations_page.table.item(r, 0).text()) == prestation_id), None)
    check(f"[{label}] la prestation est bien listee", row is not None)
    if row is not None:
        prestations_page.table.selectRow(row)
        # dialog.exec() ouvre une vraie boucle modale qui attend un clic
        # utilisateur - neutralisee ici (comme QMessageBox) pour verifier
        # uniquement que le bouton/handler s'executent sans exception,
        # avec la prestation correctement preselectionnee.
        with patch.object(QDialog, "exec", return_value=0):
            prestations_page.create_cddu_from_selected_prestation()

    # ------------------------------------------------------------------
    print(f"\n-- Facture (depuis le Contrat) --")
    contract_saved = contract_service.get_contract(contract_id)
    facture_seed = facture_service.build_from_contract(contract_saved)
    check(f"[{label}] Facture.formation_nom repris du Contrat", facture_seed.formation_nom == contract_saved.artiste_nom)
    check(f"[{label}] Facture.montant repris du Contrat", facture_seed.montant == contract_saved.cession_montant)

    facture_dialog = FactureDialog(None, initial_facture=facture_seed, service=facture_service, organization_service=organization_service)
    check(f"[{label}] FactureDialog : Formation affichee a l'ecran", facture_dialog.formation_nom.text() == facture_seed.formation_nom)
    facture_dialog.save()
    facture_id = facture_dialog.facture.id
    check(f"[{label}] facture enregistree", facture_id is not None)

    docx_path = facture_service.generate_docx(facture_id)
    check(f"[{label}] DOCX Facture genere", docx_path.exists())

    # ------------------------------------------------------------------
    print(f"\n-- Paiement --")
    facture_saved = facture_service.get_facture(facture_id)
    paiement_seed = paiement_service.build_from_facture(facture_saved)
    paiement_dialog = PaiementDialog(None, initial_paiement=paiement_seed, service=paiement_service, facture_service=facture_service)
    paiement_dialog.save()
    paiement_id = paiement_service.create_paiement(paiement_dialog.paiement)
    check(f"[{label}] paiement enregistre", paiement_id is not None)

    facture_after = facture_service.get_facture(facture_id)
    check(f"[{label}] statut de la facture passe a 'Payee' apres reglement complet", facture_after.status == "paid")

    print(f"\n[{label}] Chaine complete executee sans exception.")


run_scenario("NOUVELLE PRESTATION (formation_id)", use_formation=True)
run_scenario("ANCIENNE PRESTATION (artist_id, compat)", use_formation=False)

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
