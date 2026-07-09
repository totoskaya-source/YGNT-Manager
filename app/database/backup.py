from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path

from app.database.database import DB_PATH, PROJECT_ROOT, Database

BACKUP_DIR = PROJECT_ROOT / "backup"
MAX_BACKUPS = 10


def backup_database() -> Path | None:
    """Sauvegarde automatique de la base SQLite au demarrage de l'application.
    Cree backup/ si necessaire, conserve les 10 sauvegardes les plus recentes
    et supprime automatiquement les plus anciennes."""
    if not DB_PATH.exists():
        return None

    BACKUP_DIR.mkdir(exist_ok=True)

    # Force l'ecriture des transactions en attente (mode WAL) dans le fichier
    # principal, pour obtenir une sauvegarde autonome et coherente.
    try:
        Database.instance().execute("PRAGMA wal_checkpoint(FULL)")
    except Exception:
        pass

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = BACKUP_DIR / f"{DB_PATH.stem}_{timestamp}{DB_PATH.suffix}"
    shutil.copy2(DB_PATH, destination)

    _prune_old_backups()
    return destination


def _prune_old_backups() -> None:
    backups = sorted(
        BACKUP_DIR.glob(f"{DB_PATH.stem}_*{DB_PATH.suffix}"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for old_backup in backups[MAX_BACKUPS:]:
        old_backup.unlink(missing_ok=True)
