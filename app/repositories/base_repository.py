from app.database.database import Database


class BaseRepository:
    """Classe de base de tous les repositories."""

    def __init__(self):
        self.db = Database.instance()

    def execute(self, sql: str, params=()):
        return self.db.execute(sql, params)

    def executemany(self, sql: str, params):
        return self.db.executemany(sql, params)

    def fetch_one(self, sql: str, params=()):
        return self.db.fetchone(sql, params)

    def fetch_all(self, sql: str, params=()):
        return self.db.fetchall(sql, params)
    
