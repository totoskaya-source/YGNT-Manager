"""Tests de sécurité multi-tenant pour le module Prestations (Sprint 2) :
même discipline que tests/unit/test_isolation_multi_tenant.py (T4) —
attaque directe du Repository (bug applicatif hypothétique) et attaque via
le Service avec un contexte de tenant authentique mais une ressource
empruntée à une autre Société."""

import pytest

from ygnt_web.domain.exceptions import PrestationInexistante
from ygnt_web.repositories.prestation_repository import PrestationRepository
from ygnt_web.services.prestation_service import PrestationService
from ygnt_web.services.societe_service import SocieteService


def _deux_societes(connection):
    societe_a = SocieteService(connection).creer_societe(nom="Société A")
    societe_b = SocieteService(connection).creer_societe(nom="Société B")
    return societe_a, societe_b


def test_repository_obtenir_ne_renvoie_rien_hors_de_sa_societe(connection):
    societe_a, societe_b = _deux_societes(connection)
    service = PrestationService(connection)
    prestation_a = service.creer_prestation(societe_id=societe_a.id, nom="Concert A", date_debut="2026-05-10")

    repository = PrestationRepository(connection)
    assert repository.obtenir(societe_b.id, prestation_a.id) is None
    assert repository.obtenir(societe_a.id, prestation_a.id) is not None


def test_repository_modifier_refuse_hors_de_sa_societe(connection):
    societe_a, societe_b = _deux_societes(connection)
    service = PrestationService(connection)
    prestation_a = service.creer_prestation(societe_id=societe_a.id, nom="Concert A", date_debut="2026-05-10")

    repository = PrestationRepository(connection)
    resultat = repository.modifier(societe_b.id, prestation_a.id, nom="Piratee")

    assert resultat is None
    assert repository.obtenir(societe_a.id, prestation_a.id).nom == "Concert A"


def test_repository_supprimer_refuse_hors_de_sa_societe(connection):
    societe_a, societe_b = _deux_societes(connection)
    service = PrestationService(connection)
    prestation_a = service.creer_prestation(societe_id=societe_a.id, nom="Concert A", date_debut="2026-05-10")

    repository = PrestationRepository(connection)
    assert repository.supprimer(societe_b.id, prestation_a.id) is False
    assert repository.obtenir(societe_a.id, prestation_a.id) is not None


def test_service_obtenir_prestation_dune_autre_societe_est_introuvable(connection):
    societe_a, societe_b = _deux_societes(connection)
    service = PrestationService(connection)
    prestation_a = service.creer_prestation(societe_id=societe_a.id, nom="Concert A", date_debut="2026-05-10")

    with pytest.raises(PrestationInexistante):
        service.obtenir_prestation(societe_b.id, prestation_a.id)


def test_service_modifier_prestation_dune_autre_societe_est_refuse(connection):
    societe_a, societe_b = _deux_societes(connection)
    service = PrestationService(connection)
    prestation_a = service.creer_prestation(societe_id=societe_a.id, nom="Concert A", date_debut="2026-05-10")

    with pytest.raises(PrestationInexistante):
        service.modifier_prestation(
            societe_b.id, prestation_a.id, nom="Piratee", date_debut="2026-01-01",
            type_evenement=prestation_a.type_evenement,
        )


def test_service_supprimer_prestation_dune_autre_societe_est_refuse(connection):
    societe_a, societe_b = _deux_societes(connection)
    service = PrestationService(connection)
    prestation_a = service.creer_prestation(societe_id=societe_a.id, nom="Concert A", date_debut="2026-05-10")

    with pytest.raises(PrestationInexistante):
        service.supprimer_prestation(societe_b.id, prestation_a.id)


def test_service_dupliquer_prestation_dune_autre_societe_est_refuse(connection):
    societe_a, societe_b = _deux_societes(connection)
    service = PrestationService(connection)
    prestation_a = service.creer_prestation(societe_id=societe_a.id, nom="Concert A", date_debut="2026-05-10")

    with pytest.raises(PrestationInexistante):
        service.dupliquer_prestation(societe_b.id, prestation_a.id)


def test_lister_prestations_ne_montre_jamais_celles_dune_autre_societe(connection):
    societe_a, societe_b = _deux_societes(connection)
    service = PrestationService(connection)
    service.creer_prestation(societe_id=societe_a.id, nom="Concert A", date_debut="2026-05-10")
    service.creer_prestation(societe_id=societe_b.id, nom="Concert B", date_debut="2026-05-10")

    resultat_a = service.lister_prestations(societe_a.id)

    assert resultat_a.total == 1
    assert resultat_a.items[0].nom == "Concert A"
