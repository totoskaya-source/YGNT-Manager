"""Resolution centralisee des chemins de l'application.

Fonctionne a l'identique en developpement (`python main.py`) et une fois
empaquete avec PyInstaller (onefile ou onedir) - c'est le seul endroit du
projet qui doit connaitre la difference entre les deux.

Deux categories de chemins, jamais interchangeables :

- `resource_path()` : ressources EN LECTURE SEULE embarquees dans le paquet
  (templates DOCX...). Une fois empaquetees, elles vivent dans le dossier
  d'extraction PyInstaller (`sys._MEIPASS`), jamais a cote de l'executable.
- `BASE_DIR` : donnees UTILISATEUR persistantes (base SQLite, exports,
  sauvegardes). Toujours a cote de l'executable (ou de la racine du projet
  en developpement), jamais a l'interieur du bundle - ces donnees sont
  ecrites par l'application et doivent survivre a une mise a jour du
  logiciel.
"""

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    """True une fois empaquete avec PyInstaller (onefile ou onedir)."""
    return bool(getattr(sys, "frozen", False))


# Dossier de reference pour les donnees UTILISATEUR (jamais les ressources
# embarquees) : le dossier contenant l'executable une fois empaquete, ou la
# racine du projet (parent de app/) en developpement.
BASE_DIR: Path = (
    Path(sys.executable).resolve().parent
    if is_frozen()
    else Path(__file__).resolve().parents[1]
)


def resource_path(*parts: str) -> Path:
    """Chemin vers une ressource EN LECTURE SEULE embarquee dans le paquet
    (ex. un template DOCX). En developpement, equivaut a un chemin relatif a
    la racine du projet. Une fois empaquete avec PyInstaller, resout vers le
    dossier d'extraction (`sys._MEIPASS`), qu'il s'agisse d'un build onefile
    ou onedir."""
    base = Path(getattr(sys, "_MEIPASS", None) or BASE_DIR)
    return base.joinpath(*parts)
