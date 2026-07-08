from __future__ import annotations

from app.models.organization import Organization
from app.repositories.organization_repository import OrganizationRepository


class OrganizationService:
    def __init__(self, repository: OrganizationRepository | None = None) -> None:
        self.repository = repository or OrganizationRepository()

    def list_organizations(self) -> list[Organization]:
        return self.repository.get_all()

    def search_organizations(self, query: str) -> list[Organization]:
        normalized_query = query.strip().casefold()

        if not normalized_query:
            return self.list_organizations()

        return [
            organization
            for organization in self.list_organizations()
            if normalized_query in self._search_text(organization)
        ]

    def get_organization(self, organization_id: int) -> Organization | None:
        return self.repository.get_by_id(organization_id)

    def create_organization(self, organization: Organization) -> int:
        self._validate(organization)
        return self.repository.insert(organization)

    def update_organization(self, organization: Organization) -> None:
        if organization.id is None:
            raise ValueError("Impossible de modifier un organisateur sans identifiant.")

        self._validate(organization)
        self.repository.update(organization)

    def delete_organization(self, organization_id: int) -> None:
        self.repository.delete(organization_id)

    def _validate(self, organization: Organization) -> None:
        if not organization.name.strip():
            raise ValueError("Le nom de l'organisateur est obligatoire.")

        organization.name = organization.name.strip()
        organization.legal_form = organization.legal_form.strip()
        organization.address = organization.address.strip()
        organization.postal_code = organization.postal_code.strip()
        organization.city = organization.city.strip()
        organization.siret = organization.siret.strip()
        organization.ape = organization.ape.strip()
        organization.licence = organization.licence.strip()
        organization.email = organization.email.strip()
        organization.phone = organization.phone.strip()
        organization.iban = organization.iban.strip()
        organization.bic = organization.bic.strip()
        organization.president = organization.president.strip()
        organization.notes = organization.notes.strip()

    def _search_text(self, organization: Organization) -> str:
        values = (
            organization.name,
            organization.legal_form,
            organization.siret,
            organization.email,
            organization.phone,
            organization.city,
            organization.president,
            organization.notes,
        )
        return " ".join(str(value or "") for value in values).casefold()
