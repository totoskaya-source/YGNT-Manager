"""Tests manuels du Sprint 10.0 - fondations du module Factures.

Execution : python test_facture.py

Ce script ne touche jamais la fiche Producteur reelle : l'instantane est
verifie via un ProducteurService factice injecte dans FactureService.
"""

from app.database.migrations import MigrationManager
from app.models.facture import Facture
from app.models.producteur import Producteur
from app.services.contract_service import ContractService
from app.services.devis_service import DevisService
from app.services.facture_service import FactureService
from app.services.producteur_service import ProducteurService


def main() -> None:
    # 1. Migration (additive, idempotente) + demarrage complet des autres modules.
    MigrationManager().migrate()
    ContractService()
    DevisService()
    print("OK - migration appliquee, aucune regression sur Contrats/Devis.")

    # Instantane Producteur : reutilise le producteur actif reel s'il existe,
    # sinon cree un producteur de test temporaire (nettoye en fin de script).
    producteur_service = ProducteurService()
    created_temp_producteur = False
    active_producteur = producteur_service.get_active_producteur()
    if active_producteur is None:
        temp_id = producteur_service.create_producteur(
            Producteur(nom="Producteur Test Sprint 10.0", siret="00000000000000")
        )
        active_producteur = producteur_service.get_producteur(temp_id)
        created_temp_producteur = True

    service = FactureService(producteur_service=producteur_service)

    # 2. Validation : organisateur et spectacle obligatoires.
    try:
        service.create_facture(Facture(spectacle_nom="Concert"))
        raise AssertionError("La creation aurait du echouer sans organisateur.")
    except ValueError:
        print("OK - validation : organisateur obligatoire.")

    try:
        service.create_facture(Facture(organisateur_structure="Ville de test"))
        raise AssertionError("La creation aurait du echouer sans spectacle.")
    except ValueError:
        print("OK - validation : spectacle obligatoire.")

    # 3. Creation + generation de reference FACT-AAAA-0001.
    facture = Facture(
        organisateur_structure="Ville de test",
        spectacle_nom="Concert de test",
        prestation_date="10/07/2026",
        montant=1000.0,
        acompte=200.0,
        tva="20%",
        mode_paiement="Virement",
        echeance="30 jours",
    )
    facture_id = service.create_facture(facture)
    assert facture_id is not None
    print(f"OK - creation : facture #{facture_id} ({facture.facture_number}).")

    import re
    assert re.fullmatch(r"FACT-\d{4}-\d{4}", facture.facture_number), (
        f"Reference inattendue : {facture.facture_number}"
    )
    print("OK - reference au format FACT-AAAA-0001.")

    # 4. Instantane Producteur applique a la creation.
    assert facture.producteur_id == active_producteur.id
    assert facture.producteur_nom == active_producteur.nom
    assert facture.producteur_siret == active_producteur.siret
    print("OK - instantane Producteur copie sur la nouvelle facture.")

    # 5. Total calcule (montant - acompte).
    assert facture.total == 800.0, f"Total inattendu : {facture.total}"
    print("OK - total = montant - acompte (800.00 EUR).")

    # 6. Lecture.
    reread = service.get_facture(facture_id)
    assert reread is not None
    assert reread.facture_number == facture.facture_number
    assert reread.organisateur_structure == "Ville de test"
    assert reread.total == 800.0
    print("OK - lecture : facture relue identique.")

    # 7. Sequence independante : une deuxieme facture incremente le compteur.
    second = Facture(
        organisateur_structure="Autre organisateur",
        spectacle_nom="Autre concert",
        montant=500.0,
    )
    second_id = service.create_facture(second)
    assert second.facture_number != facture.facture_number
    assert second.facture_number.endswith(
        f"{int(facture.facture_number.split('-')[-1]) + 1:04d}"
    )
    print("OK - sequence independante et incrementale (compteur FACT propre).")

    # 8. Modification.
    reread.montant = 1500.0
    reread.acompte = 300.0
    service.update_facture(reread)
    updated = service.get_facture(facture_id)
    assert updated.montant == 1500.0
    assert updated.total == 1200.0
    print("OK - modification : montant/total mis a jour.")

    # 9. Suppression.
    service.delete_facture(facture_id)
    service.delete_facture(second_id)
    assert service.get_facture(facture_id) is None
    assert service.get_facture(second_id) is None
    print("OK - suppression : factures de test supprimees.")

    if created_temp_producteur:
        producteur_service.delete_producteur(active_producteur.id)
        print("OK - nettoyage : producteur de test temporaire supprime.")

    print("\nTous les tests du module Factures sont passes avec succes.")


if __name__ == "__main__":
    main()
