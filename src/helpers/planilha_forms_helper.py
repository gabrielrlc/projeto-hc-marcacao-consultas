"""
Helper de Leitura da Planilha do Google Forms (CSV / XLSX)
==========================================================
Lê **em memória** (sem alterar o arquivo original) a planilha exportada do
Google Forms e devolve linhas padronizadas com os campos internos do sistema.

Os cabeçalhos do Forms são o texto das perguntas e ainda não foram confirmados
com a Central de Marcação; por isso as colunas são reconhecidas por **aliases**
normalizados (sem acento, caixa ou pontuação) em ``ALIASES_COLUNAS``. Para
suportar um novo cabeçalho basta acrescentar o alias correspondente.

No XLSX, linhas com preenchimento verde (convenção atual da Central para
"agendado") são sinalizadas em ``marcada_agendada``.
"""

import csv
import io
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

from .string_helper import normalizar_texto, texto_ou_none

EXTENSOES_SUPORTADAS = (".csv", ".xlsx")
TAMANHO_MAXIMO_BYTES = 5 * 1024 * 1024
MAXIMO_LINHAS = 10_000


class PlanilhaInvalidaError(ValueError):
    """Erro de leitura/estrutura da planilha enviada (mensagem exibível ao usuário)."""


# campo interno -> (aliases exatos, prefixos aceitos). Comparação após normalizar_cabecalho().
ALIASES_COLUNAS: Dict[str, Tuple[Tuple[str, ...], Tuple[str, ...]]] = {
    "codigo_solicitacao": (
        ("NUMERO DA SOLICITACAO", "NO DA SOLICITACAO", "N DA SOLICITACAO", "SOLICITACAO",
         "CODIGO DA SOLICITACAO", "NUMERO SOLICITACAO", "CODIGO SOLICITACAO", "NO SOLICITACAO",
         "N SOLICITACAO"),
        ("NUMERO DA SOLICITACAO", "NO DA SOLICITACAO", "N DA SOLICITACAO", "CODIGO DA SOLICITACAO",
         "NUMERO SOLICITACAO", "NO SOLICITACAO", "N SOLICITACAO"),
    ),
    "prontuario": (
        ("NUMERO DO PRONTUARIO", "NO DO PRONTUARIO", "N DO PRONTUARIO", "PRONTUARIO"),
        ("NUMERO DO PRONTUARIO", "NO DO PRONTUARIO", "N DO PRONTUARIO"),
    ),
    "nome_paciente": (
        ("NOME DO PACIENTE", "NOME COMPLETO", "NOME COMPLETO DO PACIENTE", "NOME", "PACIENTE"),
        ("NOME DO PACIENTE", "NOME COMPLETO"),
    ),
    "exame_informado": (
        ("EXAME DESEJADO", "EXAME", "EXAMES", "QUAL EXAME", "EXAME SOLICITADO"),
        ("EXAME DESEJADO", "QUAL EXAME", "QUAL O EXAME"),
    ),
    "data_retorno": (
        ("DATA DO RETORNO", "DATA DE RETORNO", "RETORNO"),
        ("DATA DO RETORNO", "DATA DE RETORNO"),
    ),
    "telefone": (
        ("TELEFONE WHATSAPP", "TELEFONE", "WHATSAPP", "CELULAR", "TELEFONE PARA CONTATO", "CONTATO"),
        ("TELEFONE", "WHATSAPP"),
    ),
    "municipio": (
        ("MUNICIPIO", "CIDADE", "MUNICIPIO DE RESIDENCIA", "MUNICIPIO ONDE RESIDE"),
        ("MUNICIPIO", "CIDADE"),
    ),
    "idade": (("IDADE", "IDADE DO PACIENTE"), ("IDADE",)),
    "carimbo": (
        ("CARIMBO DE DATA HORA", "HORA DA SOLICITACAO", "DATA HORA", "TIMESTAMP"),
        ("CARIMBO DE DATA", "HORA DA SOLICITACAO"),
    ),
    "tfd": (("TFD", "UTILIZA TFD"), ("TFD", "UTILIZA TFD", "USA TFD")),
}

CAMPOS_OBRIGATORIOS = ("codigo_solicitacao",)

_NAO_ALFANUMERICO = re.compile(r"[^A-Z0-9]+")
_VALORES_VERDADEIROS = {"SIM", "S", "X", "TRUE", "VERDADEIRO", "1", "YES"}
_FORMATOS_DATA = ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y")
_FORMATOS_DATA_HORA = ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S")


@dataclass
class LinhaForms:
    """Linha padronizada da planilha do Forms."""

    numero_linha: int
    codigo_solicitacao_bruto: Optional[str] = None
    prontuario: Optional[str] = None
    nome_paciente: Optional[str] = None
    exame_informado: Optional[str] = None
    data_retorno: Optional[date] = None
    telefone: Optional[str] = None
    municipio: Optional[str] = None
    idade: Optional[int] = None
    carimbo: Optional[datetime] = None
    utiliza_tfd: bool = False
    marcada_agendada: bool = False


@dataclass
class ResultadoLeituraPlanilha:
    """Resultado da leitura: linhas padronizadas e diagnóstico das colunas."""

    linhas: List[LinhaForms]
    colunas_reconhecidas: Dict[str, str] = field(default_factory=dict)
    colunas_ignoradas: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Cabeçalhos
# ---------------------------------------------------------------------------


def normalizar_cabecalho(cabecalho: Any) -> str:
    """Normaliza um cabeçalho para comparação (ex: ``"Nº da Solicitação:"`` -> ``"NO DA SOLICITACAO"``)."""
    return _NAO_ALFANUMERICO.sub(" ", normalizar_texto(cabecalho)).strip()


def mapear_colunas(cabecalhos: List[Any]) -> Tuple[Dict[str, int], Dict[str, str], List[str]]:
    """
    Associa cada campo interno a um índice de coluna. Correspondências exatas
    têm precedência sobre prefixos; a primeira coluna encontrada vence.

    Returns:
        ``(indices_por_campo, cabecalho_original_por_campo, cabecalhos_ignorados)``.
    """
    normalizados = [normalizar_cabecalho(c) for c in cabecalhos]
    indices: Dict[str, int] = {}
    usados: set[int] = set()

    for modo in ("exato", "prefixo"):
        for campo, (exatos, prefixos) in ALIASES_COLUNAS.items():
            if campo in indices:
                continue
            for i, nome in enumerate(normalizados):
                if i in usados or not nome:
                    continue
                casou = nome in exatos if modo == "exato" else any(nome.startswith(p) for p in prefixos)
                if casou:
                    indices[campo] = i
                    usados.add(i)
                    break

    originais = {campo: str(cabecalhos[i]).strip() for campo, i in indices.items()}
    ignorados = [str(c).strip() for i, c in enumerate(cabecalhos) if i not in usados and texto_ou_none(c)]
    return indices, originais, ignorados


# ---------------------------------------------------------------------------
# Conversões de valores
# ---------------------------------------------------------------------------


def converter_data(valor: Any) -> Optional[date]:
    """Converte datas do Forms (``dd/mm/aaaa``, ISO ou célula de data do XLSX)."""
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = texto_ou_none(valor)
    if texto is None:
        return None
    texto = texto.split(" ")[0]
    for formato in _FORMATOS_DATA:
        try:
            return datetime.strptime(texto, formato).date()
        except ValueError:
            continue
    return None


def converter_data_hora(valor: Any) -> Optional[datetime]:
    """Converte o carimbo de data/hora do Forms."""
    if isinstance(valor, datetime):
        return valor
    texto = texto_ou_none(valor)
    if texto is None:
        return None
    for formato in _FORMATOS_DATA_HORA:
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue
    data = converter_data(texto)
    return datetime.combine(data, datetime.min.time()) if data else None


def converter_idade(valor: Any) -> Optional[int]:
    """Extrai a idade em anos (ex: ``"45 anos"`` -> ``45``); fora de 0..130 vira ``None``."""
    if isinstance(valor, (int, float)) and not isinstance(valor, bool):
        idade = int(valor)
    else:
        encontrado = re.search(r"\d+", texto_ou_none(valor) or "")
        if not encontrado:
            return None
        idade = int(encontrado.group())
    return idade if 0 <= idade <= 130 else None


def converter_booleano(valor: Any) -> bool:
    """Interpreta respostas afirmativas (``Sim``, ``S``, ``X``, ``1``...)."""
    return normalizar_texto(valor) in _VALORES_VERDADEIROS


def _texto_celula(valor: Any) -> Optional[str]:
    """Converte uma célula em texto, tratando números inteiros vindos do XLSX."""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    return texto_ou_none(valor)


def eh_cor_verde(rgb: Optional[str]) -> bool:
    """Indica se uma cor ARGB/RGB hexadecimal é predominantemente verde."""
    if not isinstance(rgb, str):
        return False
    hexa = rgb[-6:]
    if not re.fullmatch(r"[0-9A-Fa-f]{6}", hexa):
        return False
    r, g, b = (int(hexa[i:i + 2], 16) for i in (0, 2, 4))
    return g - max(r, b) >= 15


# ---------------------------------------------------------------------------
# Leitura de arquivos
# ---------------------------------------------------------------------------


def _ler_csv(conteudo: bytes) -> List[Tuple[List[Any], bool]]:
    """Lê um CSV (UTF-8 com/sem BOM ou Latin-1; separador ``,`` ou ``;``)."""
    try:
        texto = conteudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = conteudo.decode("latin-1")
    amostra = texto[:4096]
    try:
        dialeto = csv.Sniffer().sniff(amostra, delimiters=",;\t")
    except csv.Error:
        dialeto = csv.excel
    return [(linha, False) for linha in csv.reader(io.StringIO(texto), dialeto)]


def _ler_xlsx(conteudo: bytes) -> List[Tuple[List[Any], bool]]:
    """Lê a primeira aba de um XLSX, detectando linhas com preenchimento verde."""
    from openpyxl import load_workbook

    try:
        planilha = load_workbook(io.BytesIO(conteudo), read_only=False, data_only=True).worksheets[0]
    except Exception as exc:  # arquivo corrompido ou não-XLSX
        raise PlanilhaInvalidaError("Não foi possível ler o arquivo XLSX enviado.") from exc

    linhas: List[Tuple[List[Any], bool]] = []
    for linha in planilha.iter_rows():
        valores = [celula.value for celula in linha]
        verde = any(
            celula.fill is not None
            and celula.fill.fill_type == "solid"
            and eh_cor_verde(getattr(celula.fill.fgColor, "rgb", None))
            for celula in linha
        )
        linhas.append((valores, verde))
    return linhas


def ler_planilha_forms(conteudo: bytes, nome_arquivo: str) -> ResultadoLeituraPlanilha:
    """
    Lê a planilha exportada do Google Forms e devolve as linhas padronizadas.

    Raises:
        PlanilhaInvalidaError: extensão não suportada, arquivo vazio/grande demais,
            ausência de coluna obrigatória ou excesso de linhas.
    """
    nome = (nome_arquivo or "").lower()
    if not nome.endswith(EXTENSOES_SUPORTADAS):
        raise PlanilhaInvalidaError("Formato de arquivo não suportado. Envie a planilha em CSV ou XLSX.")
    if not conteudo:
        raise PlanilhaInvalidaError("O arquivo enviado está vazio.")
    if len(conteudo) > TAMANHO_MAXIMO_BYTES:
        raise PlanilhaInvalidaError("O arquivo excede o tamanho máximo de 5 MB.")

    brutas = _ler_xlsx(conteudo) if nome.endswith(".xlsx") else _ler_csv(conteudo)
    brutas = [(valores, verde) for valores, verde in brutas if any(texto_ou_none(v) for v in valores)]
    if not brutas:
        raise PlanilhaInvalidaError("A planilha não possui cabeçalho nem linhas de dados.")

    cabecalhos, _ = brutas[0]
    indices, originais, ignorados = mapear_colunas(cabecalhos)
    faltantes = [campo for campo in CAMPOS_OBRIGATORIOS if campo not in indices]
    if faltantes:
        raise PlanilhaInvalidaError(
            "Coluna obrigatória não encontrada: Número da solicitação. "
            f"Colunas lidas: {', '.join(str(c) for c in cabecalhos if texto_ou_none(c))}."
        )

    dados = brutas[1:]
    if len(dados) > MAXIMO_LINHAS:
        raise PlanilhaInvalidaError(f"A planilha excede o limite de {MAXIMO_LINHAS} linhas por importação.")

    def _valor(valores: List[Any], campo: str) -> Any:
        """Retorna o valor da coluna mapeada para o campo (ou ``None``)."""
        indice = indices.get(campo)
        return valores[indice] if indice is not None and indice < len(valores) else None

    linhas: List[LinhaForms] = []
    for posicao, (valores, verde) in enumerate(dados, start=2):
        linhas.append(
            LinhaForms(
                numero_linha=posicao,
                codigo_solicitacao_bruto=_texto_celula(_valor(valores, "codigo_solicitacao")),
                prontuario=_texto_celula(_valor(valores, "prontuario")),
                nome_paciente=_texto_celula(_valor(valores, "nome_paciente")),
                exame_informado=_texto_celula(_valor(valores, "exame_informado")),
                data_retorno=converter_data(_valor(valores, "data_retorno")),
                telefone=_texto_celula(_valor(valores, "telefone")),
                municipio=_texto_celula(_valor(valores, "municipio")),
                idade=converter_idade(_valor(valores, "idade")),
                carimbo=converter_data_hora(_valor(valores, "carimbo")),
                utiliza_tfd=converter_booleano(_valor(valores, "tfd")),
                marcada_agendada=verde,
            )
        )
    return ResultadoLeituraPlanilha(linhas=linhas, colunas_reconhecidas=originais, colunas_ignoradas=ignorados)
