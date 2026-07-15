from __future__ import annotations

from app.models.formation_artiste import FormationArtiste
from app.repositories.base_repository import BaseRepository


class FormationArtisteRepository(BaseRepository):

    def list_for_formation(self, formation_id: int) -> list[FormationArtiste]:
        rows = self.fetch_all(
            """
            SELECT *
            FROM formation_artistes
            WHERE formation_id=?
            ORDER BY ordre IS NULL, ordre, id
            """,
            (formation_id,),
        )
        return [self._from_row(row) for row in rows]

    def get_by_id(self, member_id: int) -> FormationArtiste | None:
        row = self.fetch_one(
            "SELECT * FROM formation_artistes WHERE id=?",
            (member_id,),
        )
        return self._from_row(row) if row else None

    def find(self, formation_id: int, artiste_id: int) -> FormationArtiste | None:
        row = self.fetch_one(
            """
            SELECT *
            FROM formation_artistes
            WHERE formation_id=? AND artiste_id=?
            """,
            (formation_id, artiste_id),
        )
        return self._from_row(row) if row else None

    def max_ordre(self, formation_id: int) -> int:
        row = self.fetch_one(
            "SELECT MAX(ordre) AS max_ordre FROM formation_artistes WHERE formation_id=?",
            (formation_id,),
        )
        value = row["max_ordre"] if row else None
        return int(value) if value is not None else 0

    def insert(self, member: FormationArtiste) -> int:
        cursor = self.execute(
            """
            INSERT INTO formation_artistes(formation_id, artiste_id, role, ordre)
            VALUES(?, ?, ?, ?)
            """,
            (member.formation_id, member.artiste_id, member.role, member.ordre),
        )
        return int(cursor.lastrowid)

    def update(self, member: FormationArtiste) -> None:
        self.execute(
            """
            UPDATE formation_artistes
            SET role=?,
                ordre=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (member.role, member.ordre, member.id),
        )

    def delete(self, member_id: int) -> None:
        self.execute("DELETE FROM formation_artistes WHERE id=?", (member_id,))

    def _from_row(self, row) -> FormationArtiste:
        return FormationArtiste(**dict(row))
