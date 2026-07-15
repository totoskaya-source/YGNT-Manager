from __future__ import annotations

from app.models.prestation_participant import PrestationParticipant
from app.repositories.base_repository import BaseRepository


class PrestationParticipantRepository(BaseRepository):

    def get_all(self) -> list[PrestationParticipant]:
        rows = self.fetch_all(
            """
            SELECT *
            FROM prestation_participants
            ORDER BY prestation_id, ordre IS NULL, ordre, id
            """
        )
        return [self._from_row(row) for row in rows]

    def get_by_id(self, participant_id: int) -> PrestationParticipant | None:
        row = self.fetch_one(
            "SELECT * FROM prestation_participants WHERE id=?",
            (participant_id,),
        )
        return self._from_row(row) if row else None

    def list_for_prestation(self, prestation_id: int) -> list[PrestationParticipant]:
        rows = self.fetch_all(
            """
            SELECT *
            FROM prestation_participants
            WHERE prestation_id=?
            ORDER BY ordre IS NULL, ordre, id
            """,
            (prestation_id,),
        )
        return [self._from_row(row) for row in rows]

    def list_for_artiste(self, artiste_id: int) -> list[PrestationParticipant]:
        rows = self.fetch_all(
            """
            SELECT *
            FROM prestation_participants
            WHERE artiste_id=?
            ORDER BY prestation_id
            """,
            (artiste_id,),
        )
        return [self._from_row(row) for row in rows]

    def find(self, prestation_id: int, artiste_id: int) -> PrestationParticipant | None:
        row = self.fetch_one(
            """
            SELECT *
            FROM prestation_participants
            WHERE prestation_id=? AND artiste_id=?
            """,
            (prestation_id, artiste_id),
        )
        return self._from_row(row) if row else None

    def insert(self, participant: PrestationParticipant) -> int:
        cursor = self.execute(
            """
            INSERT INTO prestation_participants(prestation_id, artiste_id, role, ordre)
            VALUES(?, ?, ?, ?)
            """,
            (participant.prestation_id, participant.artiste_id, participant.role, participant.ordre),
        )
        return int(cursor.lastrowid)

    def update(self, participant: PrestationParticipant) -> None:
        self.execute(
            """
            UPDATE prestation_participants
            SET role=?,
                ordre=?,
                updated_at=CURRENT_TIMESTAMP
            WHERE id=?
            """,
            (participant.role, participant.ordre, participant.id),
        )

    def delete(self, participant_id: int) -> None:
        self.execute("DELETE FROM prestation_participants WHERE id=?", (participant_id,))

    def delete_for_prestation_and_artiste(self, prestation_id: int, artiste_id: int) -> None:
        self.execute(
            "DELETE FROM prestation_participants WHERE prestation_id=? AND artiste_id=?",
            (prestation_id, artiste_id),
        )

    def _from_row(self, row) -> PrestationParticipant:
        return PrestationParticipant(**dict(row))
