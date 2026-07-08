from __future__ import annotations

from app.models.producteur import Producteur
from app.repositories.producteur_repository import ProducteurRepository


class ProducteurService:
    def __init__(self, repository: ProducteurRepository | None = None) -> None:
        self.repository = repository or ProducteurRepository()

    def list_producteurs(self) -> list[Producteur]:
        return self.repository.get_all()

    def search_producteurs(self, query: str) -> list[Producteur]:
        normalized_query = query.strip().casefold()

        if not normalized_query:
            return self.list_producteurs()

        return [
            producteur
            for producteur in self.list_producteurs()
            if normalized_query in self._search_text(producteur)
        ]

    def get_producteur(self, producteur_id: int) -> Producteur | None:
        return self.repository.get_by_id(producteur_id)

    def get_active_producteur(self) -> Producteur | None:
        return self.repository.get_active()

    def create_producteur(self, producteur: Producteur) -> int:
        self._validate(producteur)
        was_first = self.repository.get_active() is None

        new_id = self.repository.insert(producteur)

        # Le tout premier producteur cree devient actif automatiquement : c'est
        # le cas d'usage courant (une seule structure geree par le logiciel).
        if producteur.actif or was_first:
            self.set_active(new_id)

        return new_id

    def update_producteur(self, producteur: Producteur) -> None:
        if producteur.id is None:
            raise ValueError("Impossible de modifier un producteur sans identifiant.")

        self._validate(producteur)
        self.repository.update(producteur)

    def delete_producteur(self, producteur_id: int) -> None:
        self.repository.delete(producteur_id)

    def set_active(self, producteur_id: int) -> None:
        if self.repository.get_by_id(producteur_id) is None:
            raise ValueError("Producteur introuvable.")

        self.repository.deactivate_all()
        self.repository.activate(producteur_id)

    def _validate(self, producteur: Producteur) -> None:
        if not producteur.nom.strip():
            raise ValueError("Le nom du producteur est obligatoire.")

        producteur.nom = producteur.nom.strip()
        producteur.forme_juridique = producteur.forme_juridique.strip()
        producteur.adresse = producteur.adresse.strip()
        producteur.postal_code = producteur.postal_code.strip()
        producteur.city = producteur.city.strip()
        producteur.siret = producteur.siret.strip()
        producteur.ape = producteur.ape.strip()
        producteur.licence = producteur.licence.strip()
        producteur.tva = producteur.tva.strip()
        producteur.iban = producteur.iban.strip()
        producteur.bic = producteur.bic.strip()
        producteur.representant = producteur.representant.strip()
        producteur.fonction = producteur.fonction.strip()
        producteur.logo_path = producteur.logo_path.strip()
        producteur.site_internet = producteur.site_internet.strip()
        producteur.email = producteur.email.strip()
        producteur.phone = producteur.phone.strip()
        producteur.notes = producteur.notes.strip()

    def _search_text(self, producteur: Producteur) -> str:
        values = (
            producteur.nom,
            producteur.forme_juridique,
            producteur.siret,
            producteur.city,
            producteur.email,
            producteur.phone,
            producteur.notes,
        )
        return " ".join(str(value or "") for value in values).casefold()
