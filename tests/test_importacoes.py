"""
Testes da Importação e Higienização ``Forms × AGHU`` — TASK-007 / CARE-RF003
============================================================================
Usa o AGHU mock ``data/exames_aghu_mock.csv`` (provider CSV). Critério do
CARE-RF003: CSV sintético com 1 pedido válido, 1 duplicado, 1 com exame
divergente e 1 com código inexistente, todos classificados corretamente e
auditados em ``audit_logs``.

Referências do mock usadas nos cenários:
- 890001 (pront. 1023456): USAX + HEMO
- 890005 (pront. 1098765): RXMM1 (mamografia)
- 890009 (pront. 1128901): RMCRAN (ressonância de crânio)
- 890019 / 890020 (pront. 1194567): RXMM1 pedido por dois médicos
"""

import csv
import io
import json
from datetime import datetime
from typing import Dict, List, Optional

import pytest
from fastapi.testclient import TestClient
from openpyxl import Workbook
from openpyxl.styles import PatternFill
from sqlalchemy import select

from src.controllers.importacao_controller import RegistroFilaExistente, classificar_linhas
from src.helpers.planilha_forms_helper import LinhaForms
from src.models import AcompanhamentoFila, AuditLog, ImportacaoForms

URL = "/api/importacoes"

CABECALHO = [
    "Carimbo de data/hora",
    "Exame desejado",
    "Data do retorno com o profissional que solicitou",
    "Nome do paciente",
    "Número do prontuário",
    "Idade",
    "Município",
    "Número da solicitação",
    "Telefone/WhatsApp",
]


def _linha(
    solicitacao: str,
    exame: str = "",
    prontuario: str = "",
    carimbo: str = "20/11/2026 08:00:00",
    municipio: str = "Recife",
    idade: str = "50",
    retorno: str = "15/12/2026",
) -> List[str]:
    """Monta uma resposta do Forms na ordem de ``CABECALHO``."""
    return [carimbo, exame, retorno, "Paciente Teste", prontuario, idade, municipio, solicitacao, "(81) 98888-0000"]


def _csv(linhas: List[List[str]]) -> bytes:
    """Gera o conteúdo CSV (vírgula, UTF-8) de uma exportação do Forms."""
    buffer = io.StringIO()
    escritor = csv.writer(buffer)
    escritor.writerow(CABECALHO)
    escritor.writerows(linhas)
    return buffer.getvalue().encode("utf-8")


def _xlsx(linhas: List[List[str]], verdes=()) -> bytes:
    """Gera um XLSX do Forms; índices (base 0) em ``verdes`` recebem fundo verde."""
    wb = Workbook()
    ws = wb.active
    ws.append(CABECALHO)
    for i, linha in enumerate(linhas):
        ws.append(linha)
        if i in verdes:
            for celula in ws[i + 2]:
                celula.fill = PatternFill("solid", fgColor="FFB6D7A8")
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def _enviar(client: TestClient, headers: Dict[str, str], conteudo: bytes, nome: str = "respostas.csv"):
    """Envia a planilha para ``POST /api/importacoes/forms``."""
    tipo = "text/csv" if nome.endswith(".csv") else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return client.post(f"{URL}/forms", headers=headers, files={"arquivo": (nome, conteudo, tipo)})


def _status_por_linha(relatorio: dict) -> Dict[int, List[str]]:
    """Agrupa os status de higienização por linha da planilha."""
    resultado: Dict[int, List[str]] = {}
    for item in relatorio["itens"]:
        resultado.setdefault(item["linhaPlanilha"], []).append(item["statusHigienizacao"])
    return resultado


@pytest.fixture
def marcador(make_auth_headers) -> Dict[str, str]:
    """Cabeçalhos de um MARCADOR autenticado."""
    return make_auth_headers("MARCADOR", username="maira.marcadora")


# ---------------------------------------------------------------------------
# CARE-RF003: cenário de aceitação
# ---------------------------------------------------------------------------


def test_cenario_care_rf003_quatro_classificacoes_e_auditoria(client, marcador, app_db_sync_session) -> None:
    """1 válida, 1 duplicada, 1 divergente e 1 inexistente, com relatório e auditoria."""
    conteudo = _csv([
        _linha("890005", "Mamografia", "1098765", carimbo="20/11/2026 08:00:00"),
        _linha("890005", "Mamografia", "1098765", carimbo="21/11/2026 09:00:00"),
        _linha("890009", "Tomografia", "1128901"),
        _linha("999999", "Ultrassonografia", "1000000"),
    ])
    resp = _enviar(client, marcador, conteudo)
    assert resp.status_code == 201, resp.json()
    relatorio = resp.json()

    assert _status_por_linha(relatorio) == {
        2: ["VALIDA"], 3: ["DUPLICADA"], 4: ["DIVERGENCIA_EXAME"], 5: ["NAO_ENCONTRADA"],
    }
    assert relatorio["contadores"] == {
        "VALIDA": 1, "DUPLICADA": 1, "DIVERGENCIA_EXAME": 1, "NAO_ENCONTRADA": 1, "JA_REALIZADA": 0,
    }
    resumo = relatorio["importacao"]
    assert (resumo["totalLinhas"], resumo["totalValidas"], resumo["totalDuplicadas"], resumo["totalErros"]) == (4, 1, 1, 2)
    assert resumo["usuarioImportador"] == "maira.marcadora"

    divergente = next(i for i in relatorio["itens"] if i["statusHigienizacao"] == "DIVERGENCIA_EXAME")
    assert "RMCRAN" in divergente["observacoes"]
    assert divergente["codigoExame"] is None

    app_db_sync_session.expire_all()
    assert len(app_db_sync_session.scalars(select(AcompanhamentoFila)).all()) == 4
    [log] = app_db_sync_session.scalars(select(AuditLog)).all()
    assert (log.categoria, log.acao, log.usuario) == ("NEGOCIO_CLINICO", "IMPORTAR_PLANILHA_FORMS", "maira.marcadora")
    assert log.recurso == f"importacoes_forms:{resumo['id']}"
    assert log.ip_origem
    dados = json.loads(log.dados_novos)
    assert dados["contadores"]["VALIDA"] == 1
    assert "Paciente Teste" not in log.dados_novos  # minimização LGPD: sem dados de pacientes


def test_item_valido_enriquecido_com_aghu_e_forms(client, marcador) -> None:
    """Item válido usa identificação do AGHU e contato/município/idade/retorno do Forms."""
    conteudo = _csv([_linha("890005", "Mamografia", "1098765", municipio="Olinda", idade="52", retorno="10/12/2026")])
    [item] = _enviar(client, marcador, conteudo).json()["itens"]
    assert item["codigoExame"] == "RXMM1"
    assert item["prontuario"] == "1098765"
    assert item["nomePaciente"] != "Paciente Teste"  # nome oficial do AGHU
    assert item["unidadeSolicitante"] == "UDI: MAMOGRAFIA"
    assert item["municipio"] == "Olinda"
    assert item["regiaoGeografica"] == "RMR"
    assert item["idadeInformada"] == 52
    assert item["dataRetornoMedico"] == "2026-12-10"
    assert item["exameInformadoForms"] == "Mamografia"
    assert item["statusOperacional"] == "NA_FILA"


# ---------------------------------------------------------------------------
# Regras de higienização
# ---------------------------------------------------------------------------


def test_mesmo_exame_pedido_por_dois_medicos_e_duplicado(client, marcador) -> None:
    """Mesmo prontuário + mesmo exame em solicitações diferentes: o segundo é DUPLICADA."""
    conteudo = _csv([
        _linha("890019", "Mamografia", "1194567", carimbo="20/11/2026 08:00:00"),
        _linha("890020", "Mamografia", "1194567", carimbo="20/11/2026 10:00:00"),
    ])
    relatorio = _enviar(client, marcador, conteudo).json()
    assert _status_por_linha(relatorio) == {2: ["VALIDA"], 3: ["DUPLICADA"]}
    duplicado = next(i for i in relatorio["itens"] if i["statusHigienizacao"] == "DUPLICADA")
    assert "linha 2" in duplicado["observacoes"]


def test_ordem_cronologica_define_envio_valido(client, marcador) -> None:
    """O envio mais antigo (carimbo) é o válido, mesmo aparecendo depois no arquivo."""
    conteudo = _csv([
        _linha("890005", "Mamografia", "1098765", carimbo="22/11/2026 08:00:00"),
        _linha("890005", "Mamografia", "1098765", carimbo="20/11/2026 08:00:00"),
    ])
    assert _status_por_linha(_enviar(client, marcador, conteudo).json()) == {2: ["DUPLICADA"], 3: ["VALIDA"]}


def test_solicitacao_de_outro_prontuario_e_nao_encontrada(client, marcador) -> None:
    """Número existente, mas de outro paciente (digitação errada): NAO_ENCONTRADA."""
    [item] = _enviar(client, marcador, _csv([_linha("890005", "Mamografia", "5550001")])).json()["itens"]
    assert item["statusHigienizacao"] == "NAO_ENCONTRADA"
    assert "outro prontuário" in item["observacoes"]
    assert item["prontuario"] == "5550001"


def test_codigo_com_formatacao_e_normalizado(client, marcador) -> None:
    """Número digitado com pontuação/prefixo é reduzido aos dígitos."""
    [item] = _enviar(client, marcador, _csv([_linha("Nº 890.005", "Mamografia", "1098765")])).json()["itens"]
    assert item["statusHigienizacao"] == "VALIDA"
    assert item["codigoSolicitacao"] == "890005"


def test_solicitacao_vazia_e_nao_encontrada(client, marcador) -> None:
    """Linha sem número da solicitação é NAO_ENCONTRADA."""
    [item] = _enviar(client, marcador, _csv([_linha("", "Mamografia", "1098765")])).json()["itens"]
    assert item["statusHigienizacao"] == "NAO_ENCONTRADA"
    assert item["codigoSolicitacao"] == "NAO_INFORMADO"


def test_exame_nao_informado_gera_um_item_por_exame_da_solicitacao(client, marcador) -> None:
    """Sem exame informado, cada exame da solicitação vira um item válido."""
    relatorio = _enviar(client, marcador, _csv([_linha("890001", "", "1023456")])).json()
    assert sorted(i["codigoExame"] for i in relatorio["itens"]) == ["HEMO", "USAX"]
    assert {i["statusHigienizacao"] for i in relatorio["itens"]} == {"VALIDA"}


def test_exame_informado_seleciona_apenas_o_item_correspondente(client, marcador) -> None:
    """Solicitação com USAX + HEMO e Forms pedindo ultrassom: só USAX entra."""
    [item] = _enviar(client, marcador, _csv([_linha("890001", "USG abdome", "1023456")])).json()["itens"]
    assert item["codigoExame"] == "USAX"


def test_reimportacao_detecta_duplicidade_contra_fila(client, marcador) -> None:
    """Item já VALIDA na fila (importação anterior) vira DUPLICADA na próxima importação."""
    conteudo = _csv([_linha("890005", "Mamografia", "1098765")])
    primeiro = _enviar(client, marcador, conteudo).json()["itens"][0]
    [segundo] = _enviar(client, marcador, conteudo).json()["itens"]
    assert segundo["statusHigienizacao"] == "DUPLICADA"
    assert f"#{primeiro['id']}" in segundo["observacoes"]


def test_item_cancelado_na_fila_nao_bloqueia_reimportacao(client, marcador, app_db_sync_session) -> None:
    """Item CANCELADO não conta como duplicidade."""
    conteudo = _csv([_linha("890005", "Mamografia", "1098765")])
    primeiro = _enviar(client, marcador, conteudo).json()["itens"][0]
    registro = app_db_sync_session.get(AcompanhamentoFila, primeiro["id"])
    registro.status_operacional = "CANCELADO"
    app_db_sync_session.commit()
    assert _enviar(client, marcador, conteudo).json()["itens"][0]["statusHigienizacao"] == "VALIDA"


def test_item_confirmado_no_aghu_vira_ja_realizada(client, marcador, app_db_sync_session) -> None:
    """Item da fila já CONFIRMADO_AGENDADO_AGHU: reenvio é JA_REALIZADA."""
    conteudo = _csv([_linha("890005", "Mamografia", "1098765")])
    primeiro = _enviar(client, marcador, conteudo).json()["itens"][0]
    registro = app_db_sync_session.get(AcompanhamentoFila, primeiro["id"])
    registro.status_operacional = "CONFIRMADO_AGENDADO_AGHU"
    app_db_sync_session.commit()
    [item] = _enviar(client, marcador, conteudo).json()["itens"]
    assert item["statusHigienizacao"] == "JA_REALIZADA"


def test_xlsx_linha_verde_vira_ja_realizada(client, marcador) -> None:
    """No XLSX, a linha pintada de verde (agendada pela Central) é JA_REALIZADA."""
    conteudo = _xlsx(
        [_linha("890005", "Mamografia", "1098765"), _linha("890009", "Ressonância", "1128901")],
        verdes={0},
    )
    relatorio = _enviar(client, marcador, conteudo, "respostas.xlsx").json()
    assert _status_por_linha(relatorio) == {2: ["JA_REALIZADA"], 3: ["VALIDA"]}
    assert relatorio["importacao"]["nomeArquivo"] == "respostas.xlsx"


def test_relatorio_informa_colunas_reconhecidas_e_ignoradas(client, marcador) -> None:
    """O relatório mostra como cada coluna do Forms foi interpretada."""
    conteudo = "Número da solicitação,Exame,Como conheceu o serviço?\n890005,Mamografia,Indicação\n".encode()
    relatorio = _enviar(client, marcador, conteudo).json()
    assert relatorio["colunasReconhecidas"] == {"codigoSolicitacao": "Número da solicitação", "exameInformado": "Exame"}
    assert relatorio["colunasIgnoradas"] == ["Como conheceu o serviço?"]


# ---------------------------------------------------------------------------
# Validações de arquivo, RBAC e histórico
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "conteudo, nome",
    [(b"x,y\n1,2\n", "planilha.txt"), (b"", "vazia.csv"), (b"Nome,Exame\nA,B\n", "sem_coluna.csv")],
    ids=["extensao", "vazio", "sem-coluna"],
)
def test_arquivo_invalido_retorna_400_sem_gravar(client, marcador, app_db_sync_session, conteudo, nome) -> None:
    """Arquivo inválido retorna 400 com ``detail`` e não cria importação nem auditoria."""
    resp = _enviar(client, marcador, conteudo, nome)
    assert resp.status_code == 400
    assert "detail" in resp.json()
    app_db_sync_session.expire_all()
    assert app_db_sync_session.scalars(select(ImportacaoForms)).all() == []
    assert app_db_sync_session.scalars(select(AuditLog)).all() == []


def test_sem_arquivo_retorna_400(client, marcador) -> None:
    """Requisição sem o campo ``arquivo`` retorna 400 (validação padronizada)."""
    assert client.post(f"{URL}/forms", headers=marcador).status_code == 400


def test_sem_token_retorna_401(client) -> None:
    """Rotas de importação exigem autenticação."""
    assert client.get(URL).status_code == 401
    assert client.post(f"{URL}/forms", files={"arquivo": ("a.csv", b"x", "text/csv")}).status_code == 401


@pytest.mark.parametrize("perfil", ["CONSULTA", None])
def test_perfil_sem_operacao_retorna_403(client, make_auth_headers, perfil) -> None:
    """CONSULTA (somente leitura da fila) e usuário sem perfil não importam nem veem histórico."""
    headers = make_auth_headers(perfil)
    conteudo = _csv([_linha("890005", "Mamografia", "1098765")])
    assert _enviar(client, headers, conteudo).status_code == 403
    assert client.get(URL, headers=headers).status_code == 403


@pytest.mark.parametrize("perfil", ["MARCADOR", "GESTOR_CENTRAL", "ADMINISTRADOR"])
def test_perfis_operacionais_importam(client, make_auth_headers, perfil) -> None:
    """MARCADOR, GESTOR_CENTRAL e ADMINISTRADOR podem importar."""
    resp = _enviar(client, make_auth_headers(perfil), _csv([_linha("890005", "Mamografia", "1098765")]))
    assert resp.status_code == 201


def test_historico_e_detalhe_da_importacao(client, marcador) -> None:
    """GET lista as importações (mais recente primeiro) e GET /{id} devolve itens e contadores."""
    primeira = _enviar(client, marcador, _csv([_linha("890005", "Mamografia", "1098765")]), "lote1.csv").json()
    segunda = _enviar(client, marcador, _csv([_linha("999999", "USG")]), "lote2.csv").json()

    historico = client.get(URL, headers=marcador).json()
    assert [h["nomeArquivo"] for h in historico] == ["lote2.csv", "lote1.csv"]
    assert client.get(URL, params={"limite": 1}, headers=marcador).json()[0]["id"] == segunda["importacao"]["id"]

    detalhe = client.get(f"{URL}/{primeira['importacao']['id']}", headers=marcador).json()
    assert detalhe["contadores"]["VALIDA"] == 1
    assert [i["codigoExame"] for i in detalhe["itens"]] == ["RXMM1"]
    assert client.get(f"{URL}/99999", headers=marcador).status_code == 404


# ---------------------------------------------------------------------------
# classificar_linhas (função pura)
# ---------------------------------------------------------------------------

AGHU = {
    "100": [
        {"codigo_exame": "USAX", "nome_exame": "ULTRASSONOGRAFIA DE ABDOME", "prontuario": "1", "nome": "ANA"},
        {"codigo_exame": "HEMO", "nome_exame": "HEMOGRAMA", "prontuario": "1", "nome": "ANA"},
    ],
    "200": [{"codigo_exame": "USAX", "nome_exame": "ULTRASSONOGRAFIA DE ABDOME", "prontuario": None, "nome": "BIA"}],
}


def _lf(numero: int, solicitacao: str, exame: Optional[str] = None, prontuario: Optional[str] = None, **extra) -> LinhaForms:
    """Atalho para criar uma ``LinhaForms``."""
    return LinhaForms(numero_linha=numero, codigo_solicitacao_bruto=solicitacao, exame_informado=exame,
                      prontuario=prontuario, **extra)


def test_classificar_prontuario_ausente_no_aghu_usa_o_do_forms() -> None:
    """Quando o AGHU não traz prontuário, o do Forms é usado e não gera divergência."""
    [item] = classificar_linhas([_lf(2, "200", "USG", "777")], AGHU)
    assert (item.status_higienizacao, item.prontuario) == ("VALIDA", "777")


def test_classificar_duplicidade_contra_fila_por_prontuario() -> None:
    """Item ativo na fila com mesmo prontuário e exame (outra solicitação) torna o novo DUPLICADA."""
    fila = [RegistroFilaExistente(id=9, codigo_solicitacao="300", codigo_exame="HEMO", prontuario="1",
                                  status_operacional="AGUARDANDO_CONFIRMACAO_24H")]
    itens = classificar_linhas([_lf(2, "100")], AGHU, fila)
    assert {i.codigo_exame: i.status_higienizacao for i in itens} == {"USAX": "VALIDA", "HEMO": "DUPLICADA"}


def test_classificar_sem_carimbo_vai_para_o_fim() -> None:
    """Linhas sem carimbo são processadas após as que têm carimbo."""
    linhas = [_lf(2, "200", "USG"), _lf(3, "200", "USG", carimbo=datetime(2026, 11, 1))]
    status = {i.linha.numero_linha: i.status_higienizacao for i in classificar_linhas(linhas, AGHU)}
    assert status == {3: "VALIDA", 2: "DUPLICADA"}
