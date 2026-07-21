import pytest

from ygnt_web.domain.exceptions import NomSocieteObligatoire, SocieteInexistante
from ygnt_web.domain.societe import SocieteStatut
from ygnt_web.services.societe_service import SocieteService


def test_creer_societe_renvoie_une_societe_active(connection):
    service = SocieteService(connection)

    societe = service.creer_societe(nom="Acme Productions")

    assert societe.id is not None
    assert societe.nom == "Acme Productions"
    assert societe.statut == SocieteStatut.ACTIVE


def test_creer_societe_sans_nom_leve_une_erreur(connection):
    service = SocieteService(connection)

    with pytest.raises(NomSocieteObligatoire):
        service.creer_societe(nom="   ")


def test_obtenir_societe_inexistante_leve_une_erreur(connection):
    service = SocieteService(connection)

    with pytest.raises(SocieteInexistante):
        service.obtenir_societe(999)
