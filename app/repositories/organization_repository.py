from __future__ import annotations

from app.models.organization import Organization
from .base_repository import BaseRepository


class OrganizationRepository(BaseRepository):

    def get_all(self) -> list[Organization]:
        rows = self.fetch_all(
            """
            SELECT *
            FROM organizations
            ORDER BY name
            """
        )
        return [Organization(**dict(r)) for r in rows]

    def get_by_id(self, organization_id: int) -> Organization | None:
        row = self.fetch_one(
            "SELECT * FROM organizations WHERE id=?",
            (organization_id,)
        )
        return Organization(**dict(row)) if row else None

    def insert(self, organization: Organization) -> int:

        cursor = self.execute("""
            INSERT INTO organizations(
                name,
                legal_form,
                address,
                postal_code,
                city,
                siret,
                ape,
                licence,
                email,
                phone,
                iban,
                bic,
                president,
                notes
            )
            VALUES(
                ?,?,?,?,?,?,?,?,?,?,?,?,?,?
            )
        """, (
            organization.name,
            organization.legal_form,
            organization.address,
            organization.postal_code,
            organization.city,
            organization.siret,
            organization.ape,
            organization.licence,
            organization.email,
            organization.phone,
            organization.iban,
            organization.bic,
            organization.president,
            organization.notes
        ))

        return cursor.lastrowid

    def update(self, organization: Organization) -> None:

        self.execute("""
            UPDATE organizations SET

                name=?,
                legal_form=?,
                address=?,
                postal_code=?,
                city=?,
                siret=?,
                ape=?,
                licence=?,
                email=?,
                phone=?,
                iban=?,
                bic=?,
                president=?,
                notes=?

            WHERE id=?
        """, (

            organization.name,
            organization.legal_form,
            organization.address,
            organization.postal_code,
            organization.city,
            organization.siret,
            organization.ape,
            organization.licence,
            organization.email,
            organization.phone,
            organization.iban,
            organization.bic,
            organization.president,
            organization.notes,
            organization.id

        ))

    def delete(self, organization_id: int) -> None:

        self.execute(
            "DELETE FROM organizations WHERE id=?",
            (organization_id,)
        )
