"""Testes integrados dos nove KPIs com SQLite e relógio controlados."""

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from src.controllers import dashboard_controller
from src.models import AcompanhamentoFila

AGORA = datetime(2026, 11, 26, 12)
URL = "/api/dashboard/kpis"


@pytest.fixture(autouse=True)
def relogio_fixo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fixa o instante de referência dos cálculos sem afetar o restante do app."""
    class Relogio(datetime):
        """Relógio de teste compatível com datetime."""

        @classmethod
        def now(cls, tz: timezone | None = None) -> datetime:
            """Retorna o instante fixo no fuso solicitado."""
            return AGORA.replace(tzinfo=timezone.utc).astimezone(tz) if tz else AGORA

    monkeypatch.setattr(dashboard_controller, "datetime", Relogio)


def item(**campos: Any) -> AcompanhamentoFila:
    """Constrói um item sintético com valores padrão conhecidos."""
    valores = {
        "codigo_solicitacao": "SOL-TESTE",
        "codigo_exame": "HEMO",
        "nome_paciente": "PACIENTE SINTETICO",
        "created_at": AGORA - timedelta(days=2),
        "status_higienizacao": "VALIDA",
        "status_operacional": "NA_FILA",
    }
    valores.update(campos)
    return AcompanhamentoFila(**valores)


def test_kpis_banco_vazio(client: TestClient, admin_headers: dict[str, str]) -> None:
    """Retorna exatamente os nove campos do contrato, sem NaN ou divisões por zero."""
    response = client.get(URL, headers=admin_headers)
    assert response.status_code == 200
    assert response.json() == {
        "totalNaFila": 0,
        "aguardando24h": 0,
        "prazo24hVencidos": 0,
        "confirmadosAgendados": 0,
        "duplicidadesBarradas": 0,
        "divergenciasDetectadas": 0,
        "tempoMedioEsperaDias": 0.0,
        "filaPorExame": [],
        "filaPorRegiao": [],
    }


def test_kpis_estados_mistos_e_exclusao_logica(
    client: TestClient, indicadores_db: Session, admin_headers: dict[str, str]
) -> None:
    """Separa estados, ignora exclusões e calcula agrupamentos determinísticos."""
    registros = [
        item(regiao_geografica="CAPITAL"),
        item(regiao_geografica="CAPITAL", created_at=AGORA - timedelta(days=4)),
        item(codigo_exame="USAX", regiao_geografica="RMR", created_at=AGORA - timedelta(days=1)),
        item(codigo_exame=None, created_at=AGORA - timedelta(days=1)),
        item(status_operacional="CONFIRMADO_AGENDADO_AGHU"),
        item(status_higienizacao="DUPLICADA"),
        item(status_higienizacao="DIVERGENCIA_EXAME"),
        item(status_higienizacao="NAO_ENCONTRADA"),
        item(status_higienizacao="JA_REALIZADA"),
        item(status_operacional="CANCELADO"),
        item(status_operacional="SEM_RESPOSTA_24H"),
        item(status_higienizacao="NAO_ENCONTRADA", status_operacional="CONFIRMADO_AGENDADO_AGHU"),
    ]
    for prazo in (AGORA - timedelta(seconds=1), AGORA, AGORA + timedelta(seconds=1), None):
        registros.append(item(status_operacional="AGUARDANDO_CONFIRMACAO_24H", prazo_confirmacao_em=prazo))
    # Cada contador deve desconsiderar seu respectivo registro excluído.
    for registro in list(registros):
        registros.append(item(
            status_operacional=registro.status_operacional,
            status_higienizacao=registro.status_higienizacao,
            prazo_confirmacao_em=registro.prazo_confirmacao_em,
            created_at=AGORA - timedelta(days=100),
            deleted_at=AGORA,
        ))
    indicadores_db.add_all(registros)
    indicadores_db.commit()

    response = client.get(URL, headers=admin_headers)
    assert response.status_code == 200
    assert response.json() == {
        "totalNaFila": 4,
        "aguardando24h": 4,
        "prazo24hVencidos": 2,
        "confirmadosAgendados": 1,
        "duplicidadesBarradas": 1,
        "divergenciasDetectadas": 1,
        "tempoMedioEsperaDias": 2.0,
        "filaPorExame": [
            {"exame": "HEMO", "quantidade": 2},
            {"exame": "NAO_INFORMADO", "quantidade": 1},
            {"exame": "USAX", "quantidade": 1},
        ],
        "filaPorRegiao": [
            {"regiao": "CAPITAL", "quantidade": 2},
            {"regiao": "NAO_INFORMADO", "quantidade": 1},
            {"regiao": "RMR", "quantidade": 1},
        ],
    }


def test_kpis_periodo_inclusivo_fuso_e_exame(
    client: TestClient, indicadores_db: Session, admin_headers: dict[str, str]
) -> None:
    """Aplica os filtros a contagens, qualidade, média e distribuições."""
    inicio, fim = AGORA - timedelta(days=3), AGORA - timedelta(days=1)
    registros = [item(created_at=inicio), item(created_at=fim)]
    registros += [
        item(created_at=inicio - timedelta(microseconds=1)),
        item(created_at=fim + timedelta(microseconds=1)),
        item(codigo_exame="USAX"),
        item(status_higienizacao="DUPLICADA"),
        item(status_higienizacao="DIVERGENCIA_EXAME"),
        item(status_operacional="CONFIRMADO_AGENDADO_AGHU"),
        item(status_operacional="AGUARDANDO_CONFIRMACAO_24H", prazo_confirmacao_em=AGORA),
    ]
    for status in ("DUPLICADA", "DIVERGENCIA_EXAME"):
        registros += [item(status_higienizacao=status, codigo_exame="USAX"),
                      item(status_higienizacao=status, created_at=inicio - timedelta(days=1))]
    indicadores_db.add_all(registros)
    indicadores_db.commit()
    response = client.get(URL, headers=admin_headers, params={
        "data_inicio": "2026-11-23T09:00:00-03:00",
        "data_fim": "2026-11-25T12:00:00Z",
        "codigo_exame": "HEMO",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["totalNaFila"] == 2
    assert data["tempoMedioEsperaDias"] == 2.0
    assert data["duplicidadesBarradas"] == data["divergenciasDetectadas"] == 1
    assert data["confirmadosAgendados"] == data["aguardando24h"] == data["prazo24hVencidos"] == 1
    assert data["filaPorExame"] == [{"exame": "HEMO", "quantidade": 2}]
    assert data["filaPorRegiao"] == [{"regiao": "NAO_INFORMADO", "quantidade": 2}]


def test_kpis_media_arredondada_e_data_futura(
    client: TestClient, indicadores_db: Session, admin_headers: dict[str, str]
) -> None:
    """Datas futuras contribuem com zero e a média é arredondada a duas casas."""
    indicadores_db.add_all([
        item(created_at=AGORA + timedelta(days=1)),
        item(created_at=AGORA - timedelta(days=1)),
        item(created_at=AGORA - timedelta(days=1)),
    ])
    indicadores_db.commit()
    data = client.get(URL, headers=admin_headers).json()
    assert data["totalNaFila"] == 3
    assert data["tempoMedioEsperaDias"] == 0.67


@pytest.mark.parametrize("params", [
    {"data_inicio": "2026-11-27", "data_fim": "2026-11-26"},
    {"data_inicio": "invalida"},
    {"codigo_exame": ""},
])
def test_kpis_rejeita_filtros_invalidos(
    client: TestClient, admin_headers: dict[str, str], params: dict[str, str]
) -> None:
    """Mantém os erros de validação no formato textual padrão da aplicação."""
    response = client.get(URL, headers=admin_headers, params=params)
    assert response.status_code == 400
    assert isinstance(response.json()["detail"], str)


@pytest.mark.parametrize("params", [
    {"data_inicio": "2026-11-25T12:00:00Z"},
    {"data_fim": "2026-11-23T12:00:00Z"},
    {"codigo_exame": "INEXISTENTE"},
])
def test_kpis_filtros_isolados_sem_resultados(
    client: TestClient, indicadores_db: Session,
    admin_headers: dict[str, str], params: dict[str, str],
) -> None:
    """Aceita filtros individuais e não inclui itens fora do recorte."""
    indicadores_db.add(item())
    indicadores_db.commit()
    response = client.get(URL, headers=admin_headers, params=params)
    assert response.status_code == 200
    assert response.json()["totalNaFila"] == 0
    assert response.json()["filaPorExame"] == []
