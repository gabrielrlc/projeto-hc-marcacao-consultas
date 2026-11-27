"""
Testes do CRUD de Regras Configuráveis (``/api/regras``) — TASK-006 / CARE-RF009
================================================================================
Critérios de avaliação do CARE-RF009:
- bloqueio ``403`` para ``CONSULTA`` (e ``MARCADOR``) nas escritas;
- sucesso ``200/201`` para ``GESTOR_CENTRAL`` / ``ADMINISTRADOR``;
- soft delete (``deleted_at`` preenchido, sem ``DELETE`` SQL);
- registro em ``audit_logs`` (categoria ``CONFIGURACAO``) com estado anterior e novo.
"""

import json
from typing import Any, Dict, Iterator, List, Optional

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select
from sqlalchemy.orm import Session

from src.models import AuditLog, IncompatibilidadeExame, RegraExame, RegraPrioridade

BASE = "/api/regras"

NOVA_PRIORIDADE: Dict[str, Any] = {
    "codigo": "clinica_cardiologia",
    "nome": "Cardiologia",
    "tipoCriterio": "CLINICA",
    "valorMatch": "CARDIOLOGIA",
    "peso": 55,
    "ativo": True,
    "descricao": "Pacientes da cardiologia.",
}

NOVA_REGRA_EXAME: Dict[str, Any] = {
    "codigoExame": "ecg",
    "nomeExame": "Eletrocardiograma",
    "unidadeExecutora": "CARDIOLOGIA",
    "antecedenciaMinimaDias": 0,
    "janelaRetornoMaxHoras": 48,
    "exigeJejum": False,
    "priorizarManhaDiabetico": False,
    "idadeMinimaAlerta": None,
    "orientacoesPreparo": "Sem preparo.",
    "ativo": True,
}

NOVA_INCOMPATIBILIDADE: Dict[str, Any] = {
    "codigoExameOrigem": "usax",
    "codigoExameConflitante": "xyz9",
    "tipoConflito": "MESMO_DIA",
    "intervaloMinimoDias": 1,
    "motivo": "Conflito de teste.",
    "ativo": True,
}

CORPOS_POST = {
    "prioridades": NOVA_PRIORIDADE,
    "exames": NOVA_REGRA_EXAME,
    "incompatibilidades": NOVA_INCOMPATIBILIDADE,
}


# ---------------------------------------------------------------------------
# Fixtures e utilitários
# ---------------------------------------------------------------------------


@pytest.fixture
def gestor(make_auth_headers) -> Dict[str, str]:
    """Cabeçalhos de um GESTOR_CENTRAL autenticado."""
    return make_auth_headers("GESTOR_CENTRAL", username="gestor.central")


@pytest.fixture
def sql_executado(client: TestClient) -> Iterator[List[str]]:
    """Captura todas as instruções SQL emitidas pela aplicação durante o teste."""
    statements: List[str] = []
    engine = client.app.state.app_db.engine.sync_engine

    def _capturar(conn, cursor, statement, parameters, context, executemany):
        """Armazena o SQL bruto executado."""
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", _capturar)
    yield statements
    event.remove(engine, "before_cursor_execute", _capturar)


def _auditorias(session: Session, acao: Optional[str] = None) -> List[AuditLog]:
    """Retorna os registros de auditoria atuais (opcionalmente filtrados por ação)."""
    session.expire_all()
    stmt = select(AuditLog).order_by(AuditLog.id)
    if acao:
        stmt = stmt.where(AuditLog.acao == acao)
    return list(session.scalars(stmt).all())


def _id_por_codigo(session: Session, modelo, coluna, valor: str) -> int:
    """Obtém o ``id`` de um registro pelo seu código."""
    session.expire_all()
    return session.scalar(select(modelo.id).where(coluna == valor))


# ---------------------------------------------------------------------------
# Autenticação e RBAC
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("recurso", ["prioridades", "exames", "incompatibilidades"])
def test_sem_token_retorna_401(client: TestClient, recurso: str) -> None:
    """Leitura e escrita exigem autenticação (Default-Private Router)."""
    assert client.get(f"{BASE}/{recurso}").status_code == 401
    assert client.post(f"{BASE}/{recurso}", json=CORPOS_POST[recurso]).status_code == 401


@pytest.mark.parametrize("perfil", ["CONSULTA", "MARCADOR"])
@pytest.mark.parametrize("recurso", ["prioridades", "exames", "incompatibilidades"])
def test_escrita_bloqueada_para_perfis_sem_gestao(
    client: TestClient, seed_regras, make_auth_headers, app_db_sync_session, perfil: str, recurso: str
) -> None:
    """CONSULTA e MARCADOR recebem 403 em POST/PUT/DELETE e nada é auditado."""
    headers = make_auth_headers(perfil)
    assert client.post(f"{BASE}/{recurso}", json=CORPOS_POST[recurso], headers=headers).status_code == 403
    assert client.put(f"{BASE}/{recurso}/1", json=CORPOS_POST[recurso], headers=headers).status_code == 403
    resp = client.delete(f"{BASE}/{recurso}/1", headers=headers)
    assert resp.status_code == 403
    assert "detail" in resp.json()
    assert _auditorias(app_db_sync_session) == []


@pytest.mark.parametrize("perfil", ["CONSULTA", "MARCADOR", "GESTOR_CENTRAL", "ADMINISTRADOR"])
def test_leitura_liberada_para_perfis_validos(
    client: TestClient, seed_regras, make_auth_headers, perfil: str
) -> None:
    """Qualquer perfil da aplicação consulta as regras."""
    headers = make_auth_headers(perfil)
    for recurso in ("prioridades", "exames", "incompatibilidades"):
        resp = client.get(f"{BASE}/{recurso}", headers=headers)
        assert resp.status_code == 200
        assert len(resp.json()) > 0


def test_leitura_bloqueada_para_usuario_sem_perfil(client: TestClient, make_auth_headers) -> None:
    """Usuário autenticado no AD mas sem perfil local recebe 403."""
    assert client.get(f"{BASE}/prioridades", headers=make_auth_headers(None)).status_code == 403


@pytest.mark.parametrize("perfil", ["GESTOR_CENTRAL", "ADMINISTRADOR"])
@pytest.mark.parametrize("recurso", ["prioridades", "exames", "incompatibilidades"])
def test_escrita_permitida_para_gestao(
    client: TestClient, seed_regras, make_auth_headers, perfil: str, recurso: str
) -> None:
    """GESTOR_CENTRAL e ADMINISTRADOR criam registros (201)."""
    resp = client.post(f"{BASE}/{recurso}", json=CORPOS_POST[recurso], headers=make_auth_headers(perfil))
    assert resp.status_code == 201, resp.json()


# ---------------------------------------------------------------------------
# Pesos de Prioridade
# ---------------------------------------------------------------------------


def test_listar_prioridades_ordenadas_por_peso_em_camel_case(client, seed_regras, gestor) -> None:
    """A listagem retorna camelCase e ordena por peso decrescente."""
    dados = client.get(f"{BASE}/prioridades", headers=gestor).json()
    assert dados[0]["codigo"] == "CLINICA_ONCOLOGIA"
    assert {"tipoCriterio", "valorMatch", "updatedAt"} <= set(dados[0])
    pesos = [item["peso"] for item in dados]
    assert pesos == sorted(pesos, reverse=True)


def test_criar_prioridade_normaliza_codigo_e_audita(client, seed_regras, gestor, app_db_sync_session) -> None:
    """POST normaliza o código, persiste e audita CRIAR com IP e usuário."""
    resp = client.post(f"{BASE}/prioridades", json=NOVA_PRIORIDADE, headers=gestor)
    assert resp.status_code == 201
    corpo = resp.json()
    assert corpo["codigo"] == "CLINICA_CARDIOLOGIA"
    assert corpo["peso"] == 55

    [log] = _auditorias(app_db_sync_session, "CRIAR_REGRA_PRIORIDADE")
    assert log.categoria == "CONFIGURACAO"
    assert log.usuario == "gestor.central"
    assert log.recurso == f"regras_prioridade:{corpo['id']}"
    assert log.ip_origem
    assert log.dados_anteriores is None
    assert json.loads(log.dados_novos)["peso"] == 55


def test_criar_prioridade_aceita_snake_case(client, seed_regras, gestor) -> None:
    """A entrada também aceita nomes de campos em snake_case."""
    corpo = {"codigo": "GRP_X", "nome": "Grupo X", "tipo_criterio": "GRUPO_CLINICO", "valor_match": "X", "peso": 5}
    resp = client.post(f"{BASE}/prioridades", json=corpo, headers=gestor)
    assert resp.status_code == 201
    assert resp.json()["tipoCriterio"] == "GRUPO_CLINICO"


def test_criar_prioridade_codigo_duplicado_retorna_409(client, seed_regras, gestor) -> None:
    """Código já usado por regra ativa retorna 409."""
    corpo = {**NOVA_PRIORIDADE, "codigo": "clinica_oncologia"}
    resp = client.post(f"{BASE}/prioridades", json=corpo, headers=gestor)
    assert resp.status_code == 409
    assert "CLINICA_ONCOLOGIA" in resp.json()["detail"]


@pytest.mark.parametrize(
    "alteracao",
    [{"peso": -1}, {"peso": 1001}, {"tipoCriterio": "INVALIDO"}, {"nome": "ab"}, {"codigo": "x"}],
)
def test_criar_prioridade_validacoes_retornam_400(client, seed_regras, gestor, alteracao) -> None:
    """Violações do JSON Schema retornam 400 no formato ``{"detail": ...}``."""
    resp = client.post(f"{BASE}/prioridades", json={**NOVA_PRIORIDADE, **alteracao}, headers=gestor)
    assert resp.status_code == 400
    assert "detail" in resp.json()


def test_atualizar_prioridade_reflete_imediatamente_e_audita(client, seed_regras, gestor, app_db_sync_session) -> None:
    """PUT altera o peso, aparece na próxima leitura e audita antes/depois."""
    regra_id = _id_por_codigo(app_db_sync_session, RegraPrioridade, RegraPrioridade.codigo, "GRUPO_ROTINA")
    atual = client.get(f"{BASE}/prioridades/{regra_id}", headers=gestor).json()
    corpo = {k: atual[k] for k in ("nome", "tipoCriterio", "valorMatch", "ativo", "descricao")}
    corpo["peso"] = 999

    resp = client.put(f"{BASE}/prioridades/{regra_id}", json=corpo, headers=gestor)
    assert resp.status_code == 200
    assert resp.json()["codigo"] == "GRUPO_ROTINA"

    lista = client.get(f"{BASE}/prioridades", headers=gestor).json()
    assert lista[0]["id"] == regra_id

    [log] = _auditorias(app_db_sync_session, "ALTERAR_REGRA_PRIORIDADE")
    assert json.loads(log.dados_anteriores)["peso"] == atual["peso"]
    assert json.loads(log.dados_novos)["peso"] == 999


def test_atualizar_prioridade_sem_alteracao_nao_audita(client, seed_regras, gestor, app_db_sync_session) -> None:
    """PUT idêntico ao estado atual não gera auditoria."""
    atual = client.get(f"{BASE}/prioridades", headers=gestor).json()[0]
    corpo = {k: atual[k] for k in ("nome", "tipoCriterio", "valorMatch", "peso", "ativo", "descricao")}
    assert client.put(f"{BASE}/prioridades/{atual['id']}", json=corpo, headers=gestor).status_code == 200
    assert _auditorias(app_db_sync_session) == []


def test_atualizar_prioridade_inexistente_retorna_404(client, seed_regras, gestor) -> None:
    """PUT em id inexistente retorna 404."""
    corpo = {k: NOVA_PRIORIDADE[k] for k in ("nome", "tipoCriterio", "peso")}
    assert client.put(f"{BASE}/prioridades/99999", json=corpo, headers=gestor).status_code == 404


def test_excluir_prioridade_soft_delete_sem_delete_sql(
    client, seed_regras, gestor, app_db_sync_session, sql_executado
) -> None:
    """DELETE preenche deleted_at, desativa, some das leituras e não emite DELETE SQL."""
    regra_id = _id_por_codigo(app_db_sync_session, RegraPrioridade, RegraPrioridade.codigo, "VULNERAVEL_IDOSO")
    total_antes = app_db_sync_session.scalar(select(func.count()).select_from(RegraPrioridade))

    resp = client.delete(f"{BASE}/prioridades/{regra_id}", headers=gestor)
    assert resp.status_code == 204

    app_db_sync_session.expire_all()
    registro = app_db_sync_session.get(RegraPrioridade, regra_id)
    assert registro is not None
    assert registro.deleted_at is not None
    assert registro.ativo is False
    assert app_db_sync_session.scalar(select(func.count()).select_from(RegraPrioridade)) == total_antes
    assert not any(sql.lstrip().upper().startswith("DELETE") for sql in sql_executado)

    assert client.get(f"{BASE}/prioridades/{regra_id}", headers=gestor).status_code == 404
    ids = [item["id"] for item in client.get(f"{BASE}/prioridades", headers=gestor).json()]
    assert regra_id not in ids
    assert client.delete(f"{BASE}/prioridades/{regra_id}", headers=gestor).status_code == 404

    [log] = _auditorias(app_db_sync_session, "EXCLUIR_REGRA_PRIORIDADE")
    assert json.loads(log.dados_anteriores)["deleted_at"] is None
    assert json.loads(log.dados_novos)["deleted_at"] is not None


def test_recriar_codigo_excluido_reativa_registro(client, seed_regras, gestor, app_db_sync_session) -> None:
    """POST com código de regra excluída reativa o mesmo registro com os novos dados."""
    regra_id = _id_por_codigo(app_db_sync_session, RegraPrioridade, RegraPrioridade.codigo, "VULNERAVEL_IDOSO")
    client.delete(f"{BASE}/prioridades/{regra_id}", headers=gestor)

    corpo = {**NOVA_PRIORIDADE, "codigo": "vulneravel_idoso", "nome": "Idoso 60+", "peso": 45}
    resp = client.post(f"{BASE}/prioridades", json=corpo, headers=gestor)
    assert resp.status_code == 201
    assert resp.json()["id"] == regra_id
    assert resp.json()["peso"] == 45
    assert resp.json()["ativo"] is True

    [log] = _auditorias(app_db_sync_session, "REATIVAR_REGRA_PRIORIDADE")
    assert json.loads(log.dados_anteriores)["deleted_at"] is not None
    assert json.loads(log.dados_novos)["deleted_at"] is None


def test_filtro_ativo_prioridades(client, seed_regras, gestor) -> None:
    """``?ativo=false`` retorna apenas regras desativadas (sem excluí-las)."""
    atual = client.get(f"{BASE}/prioridades", headers=gestor).json()[0]
    corpo = {k: atual[k] for k in ("nome", "tipoCriterio", "valorMatch", "peso", "descricao")}
    client.put(f"{BASE}/prioridades/{atual['id']}", json={**corpo, "ativo": False}, headers=gestor)

    inativas = client.get(f"{BASE}/prioridades", params={"ativo": "false"}, headers=gestor).json()
    assert [item["id"] for item in inativas] == [atual["id"]]
    ativas = client.get(f"{BASE}/prioridades", params={"ativo": "true"}, headers=gestor).json()
    assert atual["id"] not in [item["id"] for item in ativas]


# ---------------------------------------------------------------------------
# Regras por Exame
# ---------------------------------------------------------------------------


def test_crud_regra_exame_completo(client, seed_regras, gestor, app_db_sync_session) -> None:
    """Cria, lê, atualiza e exclui logicamente uma regra de exame com auditoria."""
    resp = client.post(f"{BASE}/exames", json=NOVA_REGRA_EXAME, headers=gestor)
    assert resp.status_code == 201
    criado = resp.json()
    assert criado["codigoExame"] == "ECG"
    assert criado["janelaRetornoMaxHoras"] == 48

    assert client.get(f"{BASE}/exames/{criado['id']}", headers=gestor).json()["nomeExame"] == "Eletrocardiograma"

    corpo_put = {k: v for k, v in NOVA_REGRA_EXAME.items() if k != "codigoExame"}
    corpo_put["exigeJejum"] = True
    resp = client.put(f"{BASE}/exames/{criado['id']}", json=corpo_put, headers=gestor)
    assert resp.status_code == 200
    assert resp.json()["exigeJejum"] is True
    assert resp.json()["codigoExame"] == "ECG"

    assert client.delete(f"{BASE}/exames/{criado['id']}", headers=gestor).status_code == 204
    app_db_sync_session.expire_all()
    assert app_db_sync_session.get(RegraExame, criado["id"]).deleted_at is not None

    acoes = [log.acao for log in _auditorias(app_db_sync_session)]
    assert acoes == ["CRIAR_REGRA_EXAME", "ALTERAR_REGRA_EXAME", "EXCLUIR_REGRA_EXAME"]
    assert all(log.categoria == "CONFIGURACAO" for log in _auditorias(app_db_sync_session))


def test_regra_exame_duplicada_retorna_409(client, seed_regras, gestor) -> None:
    """Sigla de exame já cadastrada retorna 409."""
    resp = client.post(f"{BASE}/exames", json={**NOVA_REGRA_EXAME, "codigoExame": "espiro"}, headers=gestor)
    assert resp.status_code == 409


@pytest.mark.parametrize(
    "alteracao",
    [{"janelaRetornoMaxHoras": -1}, {"antecedenciaMinimaDias": -2}, {"idadeMinimaAlerta": 200}, {"codigoExame": ""}],
)
def test_regra_exame_validacoes_retornam_400(client, seed_regras, gestor, alteracao) -> None:
    """Valores fora das faixas permitidas retornam 400."""
    resp = client.post(f"{BASE}/exames", json={**NOVA_REGRA_EXAME, **alteracao}, headers=gestor)
    assert resp.status_code == 400


def test_busca_regras_exames(client, seed_regras, gestor) -> None:
    """``?busca=`` filtra por trecho do código ou do nome do exame."""
    dados = client.get(f"{BASE}/exames", params={"busca": "espiro"}, headers=gestor).json()
    assert [item["codigoExame"] for item in dados] == ["ESPIRO"]


def test_excluir_regra_exame_com_incompatibilidade_origem_retorna_409(
    client, seed_regras, gestor, app_db_sync_session
) -> None:
    """Exame origem de incompatibilidades ativas não pode ser excluído; após removê-las, pode."""
    regra_id = _id_por_codigo(app_db_sync_session, RegraExame, RegraExame.codigo_exame, "COLONO")
    resp = client.delete(f"{BASE}/exames/{regra_id}", headers=gestor)
    assert resp.status_code == 409
    assert "COLONO" in resp.json()["detail"]

    pares = client.get(f"{BASE}/incompatibilidades", params={"codigo_exame": "COLONO"}, headers=gestor).json()
    for par in (p for p in pares if p["codigoExameOrigem"] == "COLONO"):
        assert client.delete(f"{BASE}/incompatibilidades/{par['id']}", headers=gestor).status_code == 204

    assert client.delete(f"{BASE}/exames/{regra_id}", headers=gestor).status_code == 204


# ---------------------------------------------------------------------------
# Matriz de Incompatibilidades
# ---------------------------------------------------------------------------


def test_crud_incompatibilidade_completo(client, seed_regras, gestor, app_db_sync_session) -> None:
    """Cria, filtra, atualiza e exclui logicamente um par incompatível."""
    resp = client.post(f"{BASE}/incompatibilidades", json=NOVA_INCOMPATIBILIDADE, headers=gestor)
    assert resp.status_code == 201
    criado = resp.json()
    assert (criado["codigoExameOrigem"], criado["codigoExameConflitante"]) == ("USAX", "XYZ9")

    filtrados = client.get(f"{BASE}/incompatibilidades", params={"codigo_exame": "xyz9"}, headers=gestor).json()
    assert [item["id"] for item in filtrados] == [criado["id"]]

    corpo = {**NOVA_INCOMPATIBILIDADE, "tipoConflito": "INTERVALO_MINIMO", "intervaloMinimoDias": 3}
    resp = client.put(f"{BASE}/incompatibilidades/{criado['id']}", json=corpo, headers=gestor)
    assert resp.status_code == 200
    assert resp.json()["intervaloMinimoDias"] == 3

    assert client.delete(f"{BASE}/incompatibilidades/{criado['id']}", headers=gestor).status_code == 204
    app_db_sync_session.expire_all()
    registro = app_db_sync_session.get(IncompatibilidadeExame, criado["id"])
    assert registro.deleted_at is not None and registro.ativo is False

    acoes = [log.acao for log in _auditorias(app_db_sync_session)]
    assert acoes == [
        "CRIAR_INCOMPATIBILIDADE_EXAME",
        "ALTERAR_INCOMPATIBILIDADE_EXAME",
        "EXCLUIR_INCOMPATIBILIDADE_EXAME",
    ]


def test_incompatibilidade_origem_sem_regra_retorna_422(client, seed_regras, gestor) -> None:
    """Exame de origem sem regra cadastrada retorna 422."""
    corpo = {**NOVA_INCOMPATIBILIDADE, "codigoExameOrigem": "NAOEXISTE"}
    resp = client.post(f"{BASE}/incompatibilidades", json=corpo, headers=gestor)
    assert resp.status_code == 422
    assert "NAOEXISTE" in resp.json()["detail"]


def test_incompatibilidade_origem_com_regra_excluida_retorna_422(
    client, seed_regras, gestor, app_db_sync_session
) -> None:
    """Regra de exame excluída logicamente não serve como origem."""
    regra_id = _id_por_codigo(app_db_sync_session, RegraExame, RegraExame.codigo_exame, "USAX")
    assert client.delete(f"{BASE}/exames/{regra_id}", headers=gestor).status_code == 204
    resp = client.post(f"{BASE}/incompatibilidades", json=NOVA_INCOMPATIBILIDADE, headers=gestor)
    assert resp.status_code == 422


@pytest.mark.parametrize(
    "origem, conflitante",
    [("COLONO", "HEMO"), ("HEMO", "COLONO")],
    ids=["mesma-ordem", "ordem-invertida"],
)
def test_incompatibilidade_par_duplicado_retorna_409(client, seed_regras, gestor, origem, conflitante) -> None:
    """O par A×B do seed não pode ser recadastrado em nenhuma ordem."""
    corpo = {**NOVA_INCOMPATIBILIDADE, "codigoExameOrigem": origem, "codigoExameConflitante": conflitante}
    resp = client.post(f"{BASE}/incompatibilidades", json=corpo, headers=gestor)
    assert resp.status_code == 409


def test_incompatibilidade_put_para_par_existente_retorna_409(client, seed_regras, gestor) -> None:
    """PUT que transforma o par em um par já existente retorna 409."""
    criado = client.post(f"{BASE}/incompatibilidades", json=NOVA_INCOMPATIBILIDADE, headers=gestor).json()
    corpo = {**NOVA_INCOMPATIBILIDADE, "codigoExameOrigem": "COLONO", "codigoExameConflitante": "HEMO"}
    assert client.put(f"{BASE}/incompatibilidades/{criado['id']}", json=corpo, headers=gestor).status_code == 409


@pytest.mark.parametrize(
    "alteracao",
    [
        {"codigoExameConflitante": "usax"},
        {"tipoConflito": "INTERVALO_MINIMO", "intervaloMinimoDias": 0},
        {"tipoConflito": "QUALQUER"},
        {"motivo": "x"},
    ],
    ids=["mesmo-exame", "intervalo-zero", "tipo-invalido", "motivo-curto"],
)
def test_incompatibilidade_validacoes_retornam_400(client, seed_regras, gestor, alteracao) -> None:
    """Par inválido ou campos fora do contrato retornam 400."""
    resp = client.post(f"{BASE}/incompatibilidades", json={**NOVA_INCOMPATIBILIDADE, **alteracao}, headers=gestor)
    assert resp.status_code == 400
    assert "detail" in resp.json()
