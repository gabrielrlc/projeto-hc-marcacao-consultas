"""
Testes do RBAC Local (``src/auth/rbac.py``)
===========================================
Valida o mapeamento grupos do AD -> perfis, a dependência ``require_perfis``
(401 sem token, 403 sem perfil, superusuário ADMINISTRADOR) e o isolamento do
banco SQLite temporário das fixtures compartilhadas.
"""

from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.auth import rbac
from src.auth.rbac import (
    PERFIS_GESTAO,
    PERFIS_LEITURA,
    obter_usuario_logado,
    require_perfis,
    resolver_perfis,
)
from src.config import settings


@pytest.fixture
def app_rbac() -> TestClient:
    """Aplicação FastAPI mínima com rotas protegidas por perfis distintos."""
    app = FastAPI()

    @app.get("/gestao")
    async def rota_gestao(usuario: Dict[str, Any] = Depends(require_perfis(*PERFIS_GESTAO))):
        """Rota restrita a ADMINISTRADOR e GESTOR_CENTRAL."""
        return {"usuario": obter_usuario_logado(usuario), "perfis": usuario["perfis"]}

    @app.get("/marcador")
    async def rota_marcador(usuario: Dict[str, Any] = Depends(require_perfis("MARCADOR"))):
        """Rota restrita a MARCADOR (ADMINISTRADOR entra como superusuário)."""
        return {"perfis": usuario["perfis"]}

    @app.get("/leitura")
    async def rota_leitura(usuario: Dict[str, Any] = Depends(require_perfis(*PERFIS_LEITURA))):
        """Rota liberada a qualquer perfil válido da aplicação."""
        return {"perfis": usuario["perfis"]}

    return TestClient(app)


# --- resolver_perfis -------------------------------------------------------


def test_resolver_perfis_mapeia_grupos_padrao() -> None:
    """Grupos padrão de cada perfil resolvem para o perfil correspondente."""
    assert resolver_perfis(["GLO-SEC-HCPE-SETISD", "Users"]) == ["ADMINISTRADOR"]
    assert resolver_perfis(["HCPE-MARCACAO-GESTOR-CENTRAL"]) == ["GESTOR_CENTRAL"]
    assert resolver_perfis(["HCPE-MARCACAO-MARCADOR"]) == ["MARCADOR"]
    assert resolver_perfis(["HCPE-MARCACAO-CONSULTA"]) == ["CONSULTA"]


def test_resolver_perfis_ignora_caixa_espacos_e_mantem_ordem() -> None:
    """A comparação é case-insensitive e o resultado segue a ordem de PERFIS_VALIDOS."""
    perfis = resolver_perfis(["  hcpe-marcacao-consulta ", "HCPE-Marcacao-Gestor-Central"])
    assert perfis == ["GESTOR_CENTRAL", "CONSULTA"]


@pytest.mark.parametrize("grupos", [None, [], ["Users", "Domain Users"], ["", "  "]])
def test_resolver_perfis_sem_correspondencia(grupos: Any) -> None:
    """Usuário sem grupos mapeados não recebe nenhum perfil."""
    assert resolver_perfis(grupos) == []


def test_resolver_perfis_respeita_configuracao(monkeypatch: pytest.MonkeyPatch) -> None:
    """O mapeamento é lido de ``settings`` em tempo de execução."""
    monkeypatch.setattr(settings, "RBAC_GRUPOS_MARCADOR", ["GRP-A", "GRP-B"])
    assert resolver_perfis(["grp-b"]) == ["MARCADOR"]
    assert resolver_perfis(["HCPE-MARCACAO-MARCADOR"]) == []


def test_parse_lista_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Listas separadas por vírgula descartam itens vazios e espaços."""
    from src.config import _parse_lista_env

    monkeypatch.setenv("RBAC_TESTE_LISTA", " GRP-1 , ,GRP-2,")
    assert _parse_lista_env("RBAC_TESTE_LISTA") == ["GRP-1", "GRP-2"]
    assert _parse_lista_env("RBAC_TESTE_INEXISTENTE", "PADRAO") == ["PADRAO"]


# --- require_perfis --------------------------------------------------------


def test_require_perfis_rejeita_perfil_desconhecido() -> None:
    """Perfis inexistentes ou lista vazia são erros de programação."""
    with pytest.raises(ValueError):
        require_perfis("MEDICO")
    with pytest.raises(ValueError):
        require_perfis()


def test_require_perfis_sem_token_retorna_401(app_rbac: TestClient) -> None:
    """Sem Authorization, a dependência herda o 401 de ``decode_token``."""
    response = app_rbac.get("/gestao")
    assert response.status_code == 401


def test_require_perfis_token_invalido_retorna_401(app_rbac: TestClient) -> None:
    """JWT malformado retorna 401."""
    response = app_rbac.get("/gestao", headers={"Authorization": "Bearer invalido"})
    assert response.status_code == 401


@pytest.mark.parametrize("perfil", ["MARCADOR", "CONSULTA", None])
def test_require_perfis_sem_permissao_retorna_403(
    app_rbac: TestClient, make_auth_headers, perfil: Any
) -> None:
    """Perfis fora da lista (ou usuário sem perfil) recebem 403 no formato padrão."""
    response = app_rbac.get("/gestao", headers=make_auth_headers(perfil))
    assert response.status_code == 403
    assert "detail" in response.json()


def test_require_perfis_gestor_autorizado(app_rbac: TestClient, make_auth_headers) -> None:
    """GESTOR_CENTRAL acessa rota de gestão e recebe seus perfis resolvidos."""
    response = app_rbac.get(
        "/gestao", headers=make_auth_headers("GESTOR_CENTRAL", username="maira.central")
    )
    assert response.status_code == 200
    assert response.json() == {"usuario": "maira.central", "perfis": ["GESTOR_CENTRAL"]}


def test_require_perfis_administrador_e_superusuario(
    app_rbac: TestClient, make_auth_headers
) -> None:
    """ADMINISTRADOR é aceito mesmo em rota que lista apenas MARCADOR."""
    response = app_rbac.get("/marcador", headers=make_auth_headers("ADMINISTRADOR"))
    assert response.status_code == 200
    assert response.json()["perfis"] == ["ADMINISTRADOR"]


def test_require_perfis_leitura_exige_perfil_valido(
    app_rbac: TestClient, make_auth_headers
) -> None:
    """Rotas de leitura aceitam CONSULTA, mas não usuário AD sem perfil local."""
    assert app_rbac.get("/leitura", headers=make_auth_headers("CONSULTA")).status_code == 200
    assert app_rbac.get("/leitura", headers=make_auth_headers(None)).status_code == 403


def test_login_mock_admin_resolve_perfil_administrador(client: TestClient) -> None:
    """O usuário mock ``admin`` do framework resolve para ADMINISTRADOR."""
    login = client.post("/api/login", data={"username": "admin", "password": "admin"})
    token = login.json()["access_token"]
    me = client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert rbac.resolver_perfis(me.json()["groups"]) == ["ADMINISTRADOR"]


# --- Isolamento das fixtures ----------------------------------------------


def test_client_usa_banco_temporario_isolado(client: TestClient, app_db_path: Path) -> None:
    """O TestClient conecta ao SQLite temporário do teste, nunca a ``data/app.db``."""
    url = str(client.app.state.app_db.engine.url)
    assert str(app_db_path) in url
    assert "data/app.db" not in url
    assert app_db_path.exists()


def test_seed_regras_popula_banco_temporario(seed_regras, app_db_sync_session) -> None:
    """A fixture de seed grava no banco temporário, visível pela sessão síncrona."""
    from sqlalchemy import func, select

    from src.models import RegraExame, RegraPrioridade

    assert seed_regras["regras_prioridade"] > 0
    total = app_db_sync_session.scalar(select(func.count()).select_from(RegraPrioridade))
    assert total == seed_regras["regras_prioridade"]
    assert app_db_sync_session.scalar(select(func.count()).select_from(RegraExame)) > 0
