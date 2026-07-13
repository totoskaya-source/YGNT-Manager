import sqlite3
from typing import Optional

from app.paths import BASE_DIR

# PROJECT_ROOT designe le dossier de donnees UTILISATEUR (jamais les
# ressources embarquees) : la racine du projet en developpement, ou le
# dossier contenant l'executable une fois empaquete avec PyInstaller (voir
# app/paths.py). Nom conserve pour ne pas casser les imports existants
# (app.services.*).
PROJECT_ROOT = BASE_DIR
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "ygnt_manager.db"


class Database:
    _instance: Optional["Database"] = None

    def __init__(self):
        self.conn = sqlite3.connect(
            DB_PATH,
            check_same_thread=False
        )

        self.conn.row_factory = sqlite3.Row

        self._configure()

    def _configure(self):
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA synchronous = NORMAL")

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def execute(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        self.conn.commit()
        return cur

    def executemany(self, sql, params):
        cur = self.conn.cursor()
        cur.executemany(sql, params)
        self.conn.commit()
        return cur

    def fetchone(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchone()

    def fetchall(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

    def query_one(self, sql, params=()):
        return self.fetchone(sql, params)

    def query(self, sql, params=()):
        return self.fetchall(sql, params)

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        self.conn.close()
        Database._instance = None
        
