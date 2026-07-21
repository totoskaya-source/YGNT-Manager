from typing import Any, Protocol


class DatabaseConnection(Protocol):
    """Sous-ensemble de l'API utilisée par les Repositories et les migrations.

    Aucune Repository n'importe `sqlite3` directement : remplacer le moteur
    de persistance (ex. PostgreSQL) revient à fournir, uniquement dans
    `storage/database.py`, une implémentation de ce protocole pour un autre
    pilote — aucune Repository n'a à changer.

    `executescript` reste une commodité propre au pilote SQLite (plusieurs
    instructions séparées par `;` en un seul appel) ; un pilote pour un
    autre moteur devrait la fournir en exécutant les instructions une par
    une. `execute` directement sur la connexion (sans passer par un curseur
    explicite) est également une commodité SQLite : un pilote PostgreSQL
    (psycopg2/asyncpg) nécessiterait une fine couche d'adaptation exposant
    la même méthode — décision d'implémentation différée, hors périmètre
    de ce sprint.
    """

    def execute(self, sql: str, parameters: tuple = ()) -> Any: ...

    def executescript(self, sql_script: str) -> Any: ...
