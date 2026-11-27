"""Autenticação real e cabeçalhos de segurança dos novos endpoints."""

from datetime import datetime, timedelta, timezone
from typing import Callable

import jwt
import pytest
from fastapi.testclient import TestClient

import src.auth.auth as auth_module

URLS = ["/api/dashboard/kpis", "/api/admin/audit-logs"]


@pytest.mark.parametrize("url", URLS)
@pytest.mark.parametrize("tipo", ["ausente", "invalido", "expirado", "sem_grupo"])
def test_endpoints_protegidos(client: TestClient, url: str, tipo: str) -> None:
    """Bloqueia tokens ausentes, inválidos, expirados e usuários sem privilégios."""
    headers = {}
    if tipo == "invalido":
        headers = {"Authorization": "Bearer token-invalido"}
    elif tipo in ("expirado", "sem_grupo"):
        # Expiração explícita em UTC testa o consumidor sem depender do relógio
        # sem fuso utilizado pelo emissor legado do framework.
        token = jwt.encode({
            "username": "usuario.teste",
            "groups": ["Users"],
            "exp": datetime.now(timezone.utc) + timedelta(minutes=-1 if tipo == "expirado" else 5),
        }, auth_module.JWT_SECRET, algorithm="HS256")
        headers = {"Authorization": f"Bearer {token}"}
    response = client.get(url, headers=headers)
    assert response.status_code == (403 if tipo == "sem_grupo" else 401)
    assert isinstance(response.json()["detail"], str)
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "no-store" in response.headers["Cache-Control"]


@pytest.mark.parametrize("url", URLS)
def test_admin_e_security_headers(
    client: TestClient, admin_headers: dict[str, str], url: str
) -> None:
    """O grupo admin mantém acesso e todos os cinco cabeçalhos obrigatórios."""
    response = client.get(url, headers=admin_headers)
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-XSS-Protection"] == "1; mode=block"
    assert response.headers["Cache-Control"] == "no-store, no-cache, must-revalidate, max-age=0"
    assert response.headers["Pragma"] == "no-cache"


@pytest.mark.parametrize("url", URLS)
@pytest.mark.parametrize("perfil", ["GESTOR_CENTRAL", "MARCADOR", "CONSULTA"])
def test_integracao_rbac_preserva_restricao_administrativa(
    client: TestClient, make_auth_headers: Callable[..., dict[str, str]],
    url: str, perfil: str,
) -> None:
    """A integração dos perfis da master mantém a decisão de acesso da TASK-011."""
    response = client.get(url, headers=make_auth_headers(perfil))
    assert response.status_code == 403
