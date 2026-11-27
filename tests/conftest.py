"""
Fixtures Compartilhadas da Suíte Pytest
=======================================
- ``client``: TestClient da aplicação usando um SQLite **temporário e isolado
  por teste** (nunca toca em ``data/app.db``).
- ``app_db_url`` / ``app_db_path``: DSN e caminho do banco temporário do teste.
- ``seed_regras``: executa o seed inicial de regras no banco temporário.
- ``app_db_sync_session``: sessão SQLAlchemy síncrona para inspecionar o banco
  temporário nas asserções (ex: ``deleted_at`` preenchido, ``audit_logs``).
- ``make_auth_headers``: gera cabeçalhos ``Authorization`` com JWT válido para
  um perfil RBAC (``ADMINISTRADOR``, ``GESTOR_CENTRAL``, ``MARCADOR``, ``CONSULTA``).
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Callable, Dict, Iterator, List, Optional

import pytest

# Ensure src directory is in sys.path for test imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.auth.auth import auth_handler
from src.auth.rbac import obter_mapa_grupos_perfis
from src.main import app
from src.resources.seed_exames import executar_seed_cli


@pytest.fixture
def app_db_path(tmp_path: Path) -> Path:
    """Caminho do arquivo SQLite temporário exclusivo do teste."""
    return tmp_path / "app_test.db"


@pytest.fixture
def app_db_url(app_db_path: Path, monkeypatch: pytest.MonkeyPatch) -> str:
    """
    DSN assíncrono do banco temporário. Define ``SQLITE_DSN`` para que o
    ``lifespan`` de ``src/main.py`` conecte a aplicação a este banco.
    """
    url = f"sqlite+aiosqlite:///{app_db_path}"
    monkeypatch.setenv("SQLITE_DSN", url)
    return url


@pytest.fixture
def client(app_db_url: str) -> Iterator[TestClient]:
    """
    Fixture de teste que fornece um TestClient configurado para fazer requisições
    à aplicação FastAPI sobre um banco SQLite temporário e isolado.
    """
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seed_regras(client: TestClient, app_db_url: str) -> Dict[str, int]:
    """Popula o banco temporário com o seed inicial de regras de prioridade/exames."""
    return asyncio.run(executar_seed_cli(app_db_url))


@pytest.fixture
def app_db_sync_session(client: TestClient, app_db_path: Path) -> Iterator[Session]:
    """Sessão síncrona sobre o banco temporário para asserções diretas no SQLite."""
    engine = create_engine(f"sqlite:///{app_db_path}", future=True)
    try:
        with Session(engine, expire_on_commit=False) as session:
            yield session
    finally:
        engine.dispose()


@pytest.fixture
def make_auth_headers() -> Callable[..., Dict[str, str]]:
    """
    Fábrica de cabeçalhos de autenticação JWT por perfil RBAC.

    Uso::

        headers = make_auth_headers("GESTOR_CENTRAL")
        headers = make_auth_headers(None)                      # autenticado sem perfil
        headers = make_auth_headers(groups=["GRUPO-QUALQUER"])  # grupos explícitos
    """

    def _make(
        perfil: Optional[str] = "ADMINISTRADOR",
        username: Optional[str] = None,
        groups: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """Gera o cabeçalho ``Authorization: Bearer <jwt>`` para o perfil informado."""
        if groups is None:
            if perfil is None:
                groups = []
            else:
                grupos_perfil = obter_mapa_grupos_perfis()[perfil]
                if not grupos_perfil:
                    raise ValueError(f"Nenhum grupo do AD configurado para o perfil {perfil}.")
                groups = [grupos_perfil[0]]
        login = username or f"teste.{(perfil or 'sem_perfil').lower()}"
        token = auth_handler.create_access_token(
            {"username": login, "displayName": [login], "groups": groups}
        )
        return {"Authorization": f"Bearer {token}"}

    return _make
