# tests/conftest.py
import pytest
import os
import sys
import secrets
from collections.abc import Iterator
from pathlib import Path

# Ensure src directory is in sys.path for test imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from src.main import app
import src.auth.auth as auth_module
from src.auth.auth import auth_handler, MockAuthProvider


@pytest.fixture(autouse=True)
def mock_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isola autenticação dos testes do AD e das chaves do ambiente real."""
    monkeypatch.setattr(auth_handler, "provider", MockAuthProvider())
    monkeypatch.setattr(auth_module, "JWT_SECRET", secrets.token_urlsafe(32))

@pytest.fixture
def client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """
    Fixture de teste que fornece um TestClient configurado para fazer requisições à aplicação FastAPI.
    """
    dsn = f"sqlite+aiosqlite:///{tmp_path / 'app_test.db'}"
    monkeypatch.setenv("SQLITE_DSN", dsn)
    monkeypatch.setenv("APP_DB_URL", dsn)
    monkeypatch.setenv("POSTGRES_DSN", "")
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def indicadores_db(client: TestClient) -> Iterator[Session]:
    """Fornece uma sessão de preparação de dados no SQLite temporário da API."""
    engine = create_engine(f"sqlite:///{client.app.state.app_db.engine.url.database}")
    try:
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()


@pytest.fixture
def admin_headers(client: TestClient) -> dict[str, str]:
    """Autentica pelo endpoint real usando o provedor mock isolado."""
    response = client.post("/api/login", data={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
