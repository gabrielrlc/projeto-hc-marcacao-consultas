"""Integração da fila da master com os KPIs e a auditoria da TASK-011."""

from fastapi.testclient import TestClient

from tests.fila_fixtures import FilaApi, fila_api  # noqa: F401 - fixture


def test_status_da_fila_atualiza_kpis_e_consulta_de_auditoria(fila_api: FilaApi) -> None:
    """Uma mutação da fila aparece nos agregados e no endpoint de auditoria."""
    item_id = fila_api.inserir(codigo_solicitacao="900010", codigo_exame="USAX", prontuario="2002")
    client, headers = fila_api.client, fila_api.headers
    assert client.get(f"/api/exames/fila/{item_id}", headers=headers).status_code == 200
    antes = client.get("/api/dashboard/kpis", headers=headers)
    assert antes.status_code == 200
    assert antes.json()["totalNaFila"] == 1

    response = client.patch(
        f"/api/exames/fila/{item_id}/status",
        headers=headers,
        json={"statusOperacional": "AGUARDANDO_CONFIRMACAO_24H"},
    )
    assert response.status_code == 200, response.text
    depois = client.get("/api/dashboard/kpis", headers=headers)
    assert depois.status_code == 200
    assert depois.json()["totalNaFila"] == 0
    assert depois.json()["aguardando24h"] == 1
    assert depois.json()["prazo24hVencidos"] == 0

    auditoria = client.get(
        "/api/admin/audit-logs", headers=headers,
        params={"usuario": "admin", "categoria": "NEGOCIO_CLINICO"},
    )
    assert auditoria.status_code == 200
    assert auditoria.json()["total"] == 1
    log = auditoria.json()["items"][0]
    assert log["acao"] == "ALTERAR_STATUS_FILA"
    assert log["recurso"] == f"acompanhamento_fila:{item_id}"
    assert log["dados_anteriores"]["status_operacional"] == "NA_FILA"
    assert log["dados_novos"]["status_operacional"] == "AGUARDANDO_CONFIRMACAO_24H"


def test_openapi_reune_endpoints_dos_modulos_integrados(client: TestClient) -> None:
    """O app publica simultaneamente os contratos de todos os módulos integrados."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    for path, method in (
        ("/api/exames/fila", "get"),
        ("/api/exames/fila/{item_id}", "get"),
        ("/api/exames/fila/{item_id}/status", "patch"),
        ("/api/importacoes/forms", "post"),
        ("/api/importacoes", "get"),
        ("/api/regras/prioridades", "get"),
        ("/api/regras/exames", "get"),
        ("/api/regras/incompatibilidades", "get"),
        ("/api/dashboard/kpis", "get"),
        ("/api/admin/audit-logs", "get"),
    ):
        assert path in paths
        assert method in paths[path]
