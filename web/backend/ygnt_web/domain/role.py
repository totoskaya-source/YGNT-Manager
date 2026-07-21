from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Role:
    id: int
    societe_id: int
    nom: str
    description: str | None
    permissions: tuple[str, ...]
    date_creation: datetime
