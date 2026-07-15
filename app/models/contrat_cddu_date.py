from dataclasses import dataclass
from typing import Optional


@dataclass
class ContratCdduDate:
    """Une ligne = une date travaillee, la prestation d'origine dont elle
    provient, et le nombre de cachets correspondant. Voir
    docs/CDDU_ARCHITECTURE.md, §5 : source de verite unique des dates et des
    cachets d'un CDDU, qu'il soit simple (une ligne) ou mensualise
    (plusieurs lignes, potentiellement sur plusieurs prestations)."""

    id: Optional[int] = None

    contrat_cddu_id: Optional[int] = None
    prestation_id: Optional[int] = None

    date_travaillee: str = ""
    nombre_cachets: int = 1
