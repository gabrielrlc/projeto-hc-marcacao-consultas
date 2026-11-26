"""Consulta real de auditoria, filtros, paginação e imutabilidade."""

from datetime import datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.models import AuditLog

URL = "/api/admin/audit-logs"
DATA = datetime(2026, 11, 26, 12)


def evento(**campos: Any) -> AuditLog:
    """Constrói um evento sintético de auditoria."""
    valores = {
        "created_at": DATA,
        "usuario": "arthur.teste",
        "categoria": "CONFIGURACAO",
        "acao": "ALTERAR_REGRA",
        "recurso": "regra:1",
        "dados_anteriores": '{"peso": 40}',
        "dados_novos": '{"peso": 80, "descricao": "Prioridade sintética"}',
        "ip_origem": "127.0.0.1",
    }
    valores.update(campos)
    return AuditLog(**valores)


def test_auditoria_vazia(client: TestClient, admin_headers: dict[str, str]) -> None:
    """Retorna a página padrão mesmo sem eventos."""
    response = client.get(URL, headers=admin_headers)
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0, "page": 1, "page_size": 50}


def test_auditoria_paginacao_json_e_preservacao(
    client: TestClient, indicadores_db: Session, admin_headers: dict[str, str]
) -> None:
    """Ordena por data/ID, desserializa JSON e não altera nem acrescenta logs."""
    indicadores_db.add_all([
        evento(created_at=DATA - timedelta(days=1)),
        evento(dados_anteriores=None, dados_novos=None, ip_origem=None),
        evento(),
    ])
    indicadores_db.commit()
    consulta = select(AuditLog.__table__).order_by(AuditLog.id)
    antes = [dict(row) for row in indicadores_db.execute(consulta).mappings()]

    response = client.get(URL, headers=admin_headers, params={"page_size": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert [row["id"] for row in data["items"]] == [3, 2]
    primeiro, segundo = data["items"]
    assert primeiro == {
        "id": 3, "created_at": "2026-11-26T12:00:00Z",
        "usuario": "arthur.teste", "categoria": "CONFIGURACAO",
        "acao": "ALTERAR_REGRA", "recurso": "regra:1",
        "dados_anteriores": {"peso": 40},
        "dados_novos": {"peso": 80, "descricao": "Prioridade sintética"},
        "ip_origem": "127.0.0.1",
    }
    assert segundo["dados_anteriores"] is segundo["dados_novos"] is segundo["ip_origem"] is None
    pagina2 = client.get(URL, headers=admin_headers, params={"page": 2, "page_size": 2}).json()
    assert [row["id"] for row in pagina2["items"]] == [1]
    fora = client.get(URL, headers=admin_headers, params={"page": 3, "page_size": 2}).json()
    assert fora["items"] == [] and fora["total"] == 3
    depois = [dict(row) for row in indicadores_db.execute(consulta).mappings()]
    assert antes == depois


@pytest.mark.parametrize("params,ids", [
    ({"categoria": "CONFIGURACAO"}, [3, 1]),
    ({"usuario": "arthur.teste"}, [2, 1]),
    ({"usuario": "arthur"}, []),
    ({"data_inicio": "2026-11-26T09:00:00-03:00"}, [3, 2]),
    ({"data_fim": "2026-11-26T12:00:00Z"}, [2, 1]),
    ({"data_inicio": "2026-11-26T12:00:00", "data_fim": "2026-11-26T12:00:00Z"}, [2]),
    ({"categoria": "CONFIGURACAO", "usuario": "arthur.teste", "data_fim": "2026-11-26T12:00:00Z"}, [1]),
])
def test_auditoria_filtros_combinados_e_limites_inclusivos(
    client: TestClient, indicadores_db: Session, admin_headers: dict[str, str],
    params: dict[str, str], ids: list[int],
) -> None:
    """Aplica igualdade exata, AND e normalização de fuso nos limites."""
    indicadores_db.add_all([
        evento(created_at=DATA - timedelta(seconds=1)),
        evento(categoria="SEGURANCA"),
        evento(usuario="outro.teste", created_at=DATA + timedelta(seconds=1)),
    ])
    indicadores_db.commit()
    response = client.get(URL, headers=admin_headers, params=params)
    assert response.status_code == 200
    assert response.json()["total"] == len(ids)
    assert [row["id"] for row in response.json()["items"]] == ids


@pytest.mark.parametrize("params", [
    {"page": 0}, {"page_size": 0}, {"page_size": 101},
    {"page": "abc"}, {"categoria": "INVALIDA"}, {"usuario": ""},
    {"data_inicio": "invalida"},
    {"data_inicio": "2026-11-27", "data_fim": "2026-11-26"},
])
def test_auditoria_rejeita_filtros_invalidos(
    client: TestClient, admin_headers: dict[str, str], params: dict[str, str | int]
) -> None:
    """Rejeita filtros inválidos com HTTP 400 e detail textual."""
    response = client.get(URL, headers=admin_headers, params=params)
    assert response.status_code == 400
    assert isinstance(response.json()["detail"], str)


def test_auditoria_aceita_limite_maximo(client: TestClient, admin_headers: dict[str, str]) -> None:
    """Permite o tamanho máximo documentado sem truncar silenciosamente a entrada."""
    response = client.get(URL, headers=admin_headers, params={"page_size": 100})
    assert response.status_code == 200
    assert response.json()["page_size"] == 100


def test_auditoria_json_invalido_preserva_registro(
    client: TestClient, indicadores_db: Session, admin_headers: dict[str, str]
) -> None:
    """Falha de forma descritiva em log legado inválido sem expor ou reescrever o conteúdo."""
    registro = evento(dados_novos="conteudo legado invalido")
    indicadores_db.add(registro)
    indicadores_db.commit()
    response = client.get(URL, headers=admin_headers)
    assert response.status_code == 500
    assert response.json() == {"detail": "Registro de auditoria contém JSON inválido."}
    indicadores_db.refresh(registro)
    assert registro.dados_novos == "conteudo legado invalido"
