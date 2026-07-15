"""Utilitaires de dates partages, sans dependance Qt ni UI : utilisable aussi
bien par les services (ex. ContratCdduService.date_range) que par la couche
presentation (ex. app.ui.theme.DateTableWidgetItem), pour interpreter le
format francais JJ/MM/AAAA utilise partout dans l'application comme
representation texte des dates (v1.0.3, BUG-001 : le tri des tableaux se
faisait sur ce texte au lieu de la date chronologique)."""
from __future__ import annotations

import re
from datetime import date

_FRENCH_DATE_RE = re.compile(r"(\d{2})/(\d{2})/(\d{4})")


def parse_french_date(text: str | None) -> date | None:
    """Extrait la premiere date au format francais (JJ/MM/AAAA) trouvee dans
    `text` et la renvoie sous forme de date Python, ou None si le texte est
    vide ou ne contient aucune date reconnaissable. Fonctionne aussi bien
    sur une date seule ("20/08/2026") que sur une plage ("20/08/2026 -
    25/08/2026"), auquel cas la date de debut (la premiere trouvee dans le
    texte) fait foi."""
    if not text:
        return None
    match = _FRENCH_DATE_RE.search(text)
    if not match:
        return None
    day, month, year = (int(part) for part in match.groups())
    try:
        return date(year, month, day)
    except ValueError:
        return None
