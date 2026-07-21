import sqlite3

import pytest

from ygnt_web.storage.migrations import apply_schema


@pytest.fixture
def connection():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    apply_schema(conn)
    yield conn
    conn.close()
