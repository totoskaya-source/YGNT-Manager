import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from ygnt_web.core.config import get_settings
from ygnt_web.storage.connection import DatabaseConnection

# Seul module de tout le backend à importer `sqlite3` : remplacer le moteur
# de persistance se fait ici, sans modifier les Repositories (voir
# storage/connection.py).


def _connect() -> sqlite3.Connection:
    settings = get_settings()
    db_path = Path(settings.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")  # spécifique à SQLite
    return connection


@contextmanager
def get_connection() -> Iterator[DatabaseConnection]:
    connection = _connect()
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
