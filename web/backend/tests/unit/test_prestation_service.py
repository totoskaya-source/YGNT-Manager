import pytest

from ygnt_web.domain.exceptions import (
    DateDebutObligatoire,
    NomPrestationObligatoire,
    PrestationInexistante,
)
from ygnt_web.domain.prestation import PrestationStatut, TypeEvenement
from ygnt_web.services.prestation_service import PrestationService
from ygnt_web.services.societe_service import SocieteService


def _societe(connection, nom="Acme"):
    return SocieteService(connection).creer_societe(nom=nom)


def test_creer_prestation_genere_une_reference_et_un_statut_prospection(connection):
    societe = _societe(connection)
    service = PrestationService(connection)

    prestation = service.creer_prestation(
        societe_id=societe.id, nom="Concert de printemps", date_debut="2026-05-10"
    )

    assert prestation.reference == "PREST-2026-0001"
    assert prestation.statut == PrestationStatut.PROSPECTION
    assert prestation.type_evenement == TypeEvenement.AUTRE
    assert prestation.nom == "Concert de printemps"


def test_creer_prestation_incremente_la_sequence_par_annee(connection):
    societe = _societe(connection)
    service = PrestationService(connection)

    p1 = service.creer_prestation(societe_id=societe.id, nom="A", date_debut="2026-01-01")
    p2 = service.creer_prestation(societe_id=societe.id, nom="B", date_debut="2026-06-01")
    p3 = service.creer_prestation(societe_id=societe.id, nom="C", date_debut="2027-01-01")

    assert p1.reference == "PREST-2026-0001"
    assert p2.reference == "PREST-2026-0002"
    assert p3.reference == "PREST-2027-0001"


def test_creer_prestation_sans_nom_leve_une_erreur(connection):
    societe = _societe(connection)
    service = PrestationService(connection)

    with pytest.raises(NomPrestationObligatoire):
        service.creer_prestation(societe_id=societe.id, nom="   ", date_debut="2026-05-10")


def test_creer_prestation_sans_date_debut_leve_une_erreur(connection):
    societe = _societe(connection)
    service = PrestationService(connection)

    with pytest.raises(DateDebutObligatoire):
        service.creer_prestation(societe_id=societe.id, nom="Concert", date_debut="")


def test_obtenir_prestation_inexistante_leve_une_erreur(connection):
    societe = _societe(connection)
    service = PrestationService(connection)

    with pytest.raises(PrestationInexistante):
        service.obtenir_prestation(societe.id, 999)


def test_modifier_prestation_remplace_les_champs(connection):
    societe = _societe(connection)
    service = PrestationService(connection)
    prestation = service.creer_prestation(societe_id=societe.id, nom="Concert", date_debut="2026-05-10")

    modifiee = service.modifier_prestation(
        societe.id,
        prestation.id,
        nom="Concert renommé",
        date_debut="2026-05-11",
        type_evenement=TypeEvenement.FESTIVAL,
        lieu_ville="Lyon",
    )

    assert modifiee.nom == "Concert renommé"
    assert modifiee.date_debut == "2026-05-11"
    assert modifiee.type_evenement == TypeEvenement.FESTIVAL
    assert modifiee.lieu_ville == "Lyon"
    assert modifiee.reference == prestation.reference  # jamais modifiee par cette voie


def test_modifier_prestation_inexistante_leve_une_erreur(connection):
    societe = _societe(connection)
    service = PrestationService(connection)

    with pytest.raises(PrestationInexistante):
        service.modifier_prestation(
            societe.id, 999, nom="X", date_debut="2026-01-01", type_evenement=TypeEvenement.AUTRE
        )


def test_changer_statut(connection):
    societe = _societe(connection)
    service = PrestationService(connection)
    prestation = service.creer_prestation(societe_id=societe.id, nom="Concert", date_debut="2026-05-10")

    modifiee = service.changer_statut(societe.id, prestation.id, PrestationStatut.CONFIRMEE)

    assert modifiee.statut == PrestationStatut.CONFIRMEE


def test_supprimer_prestation_est_une_suppression_logique(connection):
    societe = _societe(connection)
    service = PrestationService(connection)
    prestation = service.creer_prestation(societe_id=societe.id, nom="Concert", date_debut="2026-05-10")

    service.supprimer_prestation(societe.id, prestation.id)

    with pytest.raises(PrestationInexistante):
        service.obtenir_prestation(societe.id, prestation.id)


def test_supprimer_prestation_inexistante_leve_une_erreur(connection):
    societe = _societe(connection)
    service = PrestationService(connection)

    with pytest.raises(PrestationInexistante):
        service.supprimer_prestation(societe.id, 999)


def test_dupliquer_prestation_genere_une_nouvelle_reference_et_reinitialise_le_statut(connection):
    societe = _societe(connection)
    service = PrestationService(connection)
    original = service.creer_prestation(
        societe_id=societe.id,
        nom="Concert",
        date_debut="2026-05-10",
        type_evenement=TypeEvenement.FESTIVAL,
        lieu_ville="Lyon",
    )
    service.changer_statut(societe.id, original.id, PrestationStatut.CONFIRMEE)

    copie = service.dupliquer_prestation(societe.id, original.id)

    assert copie.id != original.id
    assert copie.reference != original.reference
    assert copie.statut == PrestationStatut.PROSPECTION
    assert copie.nom == "Concert (copie)"
    assert copie.lieu_ville == "Lyon"


def test_lister_prestations_pagine(connection):
    societe = _societe(connection)
    service = PrestationService(connection)
    for i in range(5):
        service.creer_prestation(societe_id=societe.id, nom=f"Concert {i}", date_debut="2026-05-10")

    page1 = service.lister_prestations(societe.id, page=1, taille_page=2)
    page2 = service.lister_prestations(societe.id, page=2, taille_page=2)

    assert page1.total == 5
    assert len(page1.items) == 2
    assert len(page2.items) == 2
    assert {p.id for p in page1.items}.isdisjoint({p.id for p in page2.items})


def test_lister_prestations_recherche_et_filtre_statut(connection):
    societe = _societe(connection)
    service = PrestationService(connection)
    concert = service.creer_prestation(societe_id=societe.id, nom="Concert Jazz", date_debut="2026-05-10")
    service.creer_prestation(societe_id=societe.id, nom="Mariage Dupont", date_debut="2026-06-01")
    service.changer_statut(societe.id, concert.id, PrestationStatut.CONFIRMEE)

    resultat_recherche = service.lister_prestations(societe.id, recherche="Jazz")
    resultat_statut = service.lister_prestations(societe.id, statut=PrestationStatut.CONFIRMEE)

    assert [p.id for p in resultat_recherche.items] == [concert.id]
    assert [p.id for p in resultat_statut.items] == [concert.id]


def test_lister_prestations_tri(connection):
    societe = _societe(connection)
    service = PrestationService(connection)
    service.creer_prestation(societe_id=societe.id, nom="B", date_debut="2026-01-01")
    service.creer_prestation(societe_id=societe.id, nom="A", date_debut="2026-01-01")

    resultat = service.lister_prestations(societe.id, tri="nom", ordre="asc")

    assert [p.nom for p in resultat.items] == ["A", "B"]


def test_lister_prestations_exclut_les_supprimees(connection):
    societe = _societe(connection)
    service = PrestationService(connection)
    prestation = service.creer_prestation(societe_id=societe.id, nom="Concert", date_debut="2026-05-10")
    service.supprimer_prestation(societe.id, prestation.id)

    resultat = service.lister_prestations(societe.id)

    assert resultat.total == 0
