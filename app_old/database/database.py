import sqlite3
from pathlib import Path

# Dossier data
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "ygnt_manager.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS artistes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nom TEXT NOT NULL,
        prenom TEXT,
        nom_scene TEXT,
        telephone TEXT,
        email TEXT,
        adresse TEXT,
        instrument TEXT,
        role TEXT,
        statut TEXT,
        cachet REAL DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()
    