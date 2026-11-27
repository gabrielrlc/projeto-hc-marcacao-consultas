"""
Testes unitários dos helpers da importação do Forms
===================================================
- ``planilha_forms_helper``: mapeamento de cabeçalhos por aliases, leitura de
  CSV/XLSX, detecção de linha verde e conversões de valores.
- ``geografia_helper``: classificação Capital/RMR/Interior.
- ``exame_match_helper``: correspondência Forms × AGHU tolerante.
"""

import io
from datetime import date, datetime

import pytest
from openpyxl import Workbook
from openpyxl.styles import PatternFill

from src.helpers.exame_match_helper import exame_corresponde
from src.helpers.geografia_helper import classificar_regiao
from src.helpers.planilha_forms_helper import (
    PlanilhaInvalidaError,
    converter_booleano,
    converter_data,
    converter_idade,
    eh_cor_verde,
    ler_planilha_forms,
    mapear_colunas,
    normalizar_cabecalho,
)

# Cabeçalhos conforme descritos pela Central na reunião (transcrição)
CABECALHOS_REUNIAO = [
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


def _xlsx(linhas, verdes=()):
    """Gera um XLSX em memória; linhas (índice de dados, base 0) em ``verdes`` recebem fundo verde."""
    wb = Workbook()
    ws = wb.active
    for i, linha in enumerate(linhas):
        ws.append(linha)
        if i - 1 in verdes:
            for celula in ws[i + 1]:
                celula.fill = PatternFill("solid", fgColor="FFB6D7A8")
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


# --- Cabeçalhos -------------------------------------------------------------


def test_normalizar_cabecalho() -> None:
    """Remove acentos, pontuação e símbolos (``Nº`` -> ``NO``)."""
    assert normalizar_cabecalho("Nº da Solicitação:") == "NO DA SOLICITACAO"
    assert normalizar_cabecalho(" Telefone/WhatsApp ") == "TELEFONE WHATSAPP"


def test_mapear_colunas_da_reuniao() -> None:
    """Todos os campos descritos pela Central são reconhecidos."""
    indices, originais, ignorados = mapear_colunas(CABECALHOS_REUNIAO + ["Observação livre"])
    assert set(indices) == {
        "carimbo", "exame_informado", "data_retorno", "nome_paciente", "prontuario",
        "idade", "municipio", "codigo_solicitacao", "telefone",
    }
    assert originais["data_retorno"] == "Data do retorno com o profissional que solicitou"
    assert ignorados == ["Observação livre"]


def test_mapear_colunas_variacoes_da_planilha_exibida() -> None:
    """Variações citadas ao ler a planilha: 'Hora da solicitação (inclusão)', 'Exame'."""
    cab = ["Hora da solicitação (inclusão)", "Exame", "Número do prontuário", "Nome do paciente", "Nº Solicitação"]
    indices, _, _ = mapear_colunas(cab)
    assert indices == {"carimbo": 0, "exame_informado": 1, "prontuario": 2, "nome_paciente": 3, "codigo_solicitacao": 4}


# --- Leitura ---------------------------------------------------------------


def test_ler_csv_ponto_e_virgula_latin1() -> None:
    """CSV com ``;`` em Latin-1 (export comum do Excel em PT-BR) é lido corretamente."""
    texto = "Número da solicitação;Município;Idade;Data do retorno\n890001;Jaboatão;67 anos;05/12/2026\n"
    leitura = ler_planilha_forms(texto.encode("latin-1"), "respostas.csv")
    [linha] = leitura.linhas
    assert linha.codigo_solicitacao_bruto == "890001"
    assert linha.municipio == "Jaboatão"
    assert linha.idade == 67
    assert linha.data_retorno == date(2026, 12, 5)
    assert linha.numero_linha == 2


def test_ler_csv_ignora_linhas_vazias() -> None:
    """Linhas totalmente vazias não contam como dados."""
    texto = "Número da solicitação,Exame\n890001,USG\n,\n\n890002,TC\n"
    leitura = ler_planilha_forms(texto.encode(), "f.csv")
    assert [l.codigo_solicitacao_bruto for l in leitura.linhas] == ["890001", "890002"]


def test_ler_xlsx_detecta_linha_verde_e_tipos() -> None:
    """XLSX: números inteiros, datas nativas e linha verde (agendada)."""
    conteudo = _xlsx(
        [
            ["Número da solicitação", "Exame desejado", "Data do retorno", "Carimbo de data/hora"],
            [890001, "Ultrassonografia", datetime(2026, 12, 10), datetime(2026, 11, 20, 8, 30)],
            [890005, "Mamografia", "10/12/2026", None],
        ],
        verdes={1},
    )
    leitura = ler_planilha_forms(conteudo, "forms.xlsx")
    primeira, segunda = leitura.linhas
    assert primeira.codigo_solicitacao_bruto == "890001"
    assert primeira.data_retorno == date(2026, 12, 10)
    assert primeira.carimbo == datetime(2026, 11, 20, 8, 30)
    assert primeira.marcada_agendada is False
    assert segunda.marcada_agendada is True


@pytest.mark.parametrize(
    "conteudo, nome, mensagem",
    [
        (b"a,b\n1,2\n", "planilha.pdf", "Formato"),
        (b"", "vazia.csv", "vazio"),
        (b"Nome,Exame\nMaria,USG\n", "sem_solicitacao.csv", "Número da solicitação"),
        (b"nao e um xlsx", "quebrado.xlsx", "XLSX"),
        (b"x" * (5 * 1024 * 1024 + 1), "grande.csv", "5 MB"),
    ],
    ids=["extensao", "vazio", "sem-coluna-obrigatoria", "xlsx-corrompido", "tamanho"],
)
def test_ler_planilha_invalida(conteudo: bytes, nome: str, mensagem: str) -> None:
    """Arquivos inválidos geram ``PlanilhaInvalidaError`` com mensagem exibível."""
    with pytest.raises(PlanilhaInvalidaError, match=mensagem):
        ler_planilha_forms(conteudo, nome)


# --- Conversões ------------------------------------------------------------


@pytest.mark.parametrize(
    "valor, esperado",
    [("05/12/2026", date(2026, 12, 5)), ("2026-12-05", date(2026, 12, 5)), ("05/12/26", date(2026, 12, 5)),
     ("05/12/2026 10:00:00", date(2026, 12, 5)), ("amanhã", None), (None, None)],
)
def test_converter_data(valor, esperado) -> None:
    """Datas em formatos usuais do Forms; textos inválidos viram ``None``."""
    assert converter_data(valor) == esperado


@pytest.mark.parametrize("valor, esperado", [("45", 45), ("45 anos", 45), (8.0, 8), ("", None), ("200", None), ("sem", None)])
def test_converter_idade(valor, esperado) -> None:
    """Extrai a idade numérica, descartando valores implausíveis."""
    assert converter_idade(valor) == esperado


@pytest.mark.parametrize("valor, esperado", [("Sim", True), ("s", True), ("X", True), ("Não", False), (None, False)])
def test_converter_booleano(valor, esperado) -> None:
    """Interpreta respostas afirmativas."""
    assert converter_booleano(valor) is esperado


@pytest.mark.parametrize(
    "rgb, esperado",
    [("FFB6D7A8", True), ("FF00FF00", True), ("FFD9EAD3", True), ("FFFFFFFF", False), ("FFFF0000", False), (None, False)],
)
def test_eh_cor_verde(rgb, esperado) -> None:
    """Tons de verde do Google Planilhas são reconhecidos; branco/vermelho não."""
    assert eh_cor_verde(rgb) is esperado


# --- Geografia --------------------------------------------------------------


@pytest.mark.parametrize(
    "municipio, regiao",
    [("Recife", "CAPITAL"), ("recife/PE", "CAPITAL"), ("Jaboatão", "RMR"), ("Olinda - PE", "RMR"),
     ("São Lourenço da Mata", "RMR"), ("Caruaru", "INTERIOR"), ("", "NAO_INFORMADO"), (None, "NAO_INFORMADO")],
)
def test_classificar_regiao(municipio, regiao) -> None:
    """Capital, Região Metropolitana do Recife, interior ou não informado."""
    assert classificar_regiao(municipio) == regiao


# --- Correspondência de exames ---------------------------------------------

USAX = {"codigo_exame": "USAX", "nome_exame": "ULTRASSONOGRAFIA DE ABDOME TOTAL", "unidade_solicitante": "ONCOLOGIA CLINICA"}
RM = {"codigo_exame": "RMCRAN", "nome_exame": "RESSONÂNIA MAGNÉTICA DE CRÂNIO", "unidade_solicitante": "NEUROLOGIA"}
MAMO = {"codigo_exame": "RXMM1", "nome_exame": "MAMOGRAFIA BILATERAL DIGITAL", "unidade_solicitante": "UDI: MAMOGRAFIA"}


@pytest.mark.parametrize(
    "texto, item, esperado",
    [
        ("Ultrassonografia", USAX, True),
        ("ultrassom de abdômen", USAX, True),
        ("USG abdome total", USAX, True),
        ("usax", USAX, True),
        ("Tomografia", USAX, False),
        ("Ultrassonografia de tireoide", USAX, False),
        ("Ressonância magnética", RM, True),
        ("RM crânio", RM, True),
        ("Mamografia", MAMO, True),
        ("Hemograma", MAMO, False),
        ("", USAX, False),
        ("exame", USAX, False),
    ],
)
def test_exame_corresponde(texto, item, esperado) -> None:
    """Tolerância a acentos, abreviações e erros, sem aceitar exames diferentes."""
    assert exame_corresponde(texto, item) is esperado
