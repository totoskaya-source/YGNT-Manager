import pytest
from fastapi.testclient import TestClient

from ygnt_web.core.config import get_settings
from ygnt_web.storage.migrations import migrate


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "test.sqlite3"
    monkeypatch.setenv("YGNT_WEB_DB_PATH", str(db_path))
    monkeypatch.setenv("YGNT_WEB_JWT_SECRET", "test-secret-at-least-32-bytes-long")
    get_settings.cache_clear()

    migrate()

    from ygnt_web.main import app

    with TestClient(app) as test_client:
        yield test_client

    get_settings.cache_clear()
