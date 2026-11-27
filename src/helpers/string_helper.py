"""
Helper de Normalização de Textos
================================
Funções utilitárias para comparar e limpar textos vindos de fontes heterogêneas
(planilha do Google Forms, CSV/PostgreSQL do AGHU), como nomes de exames,
municípios e códigos de solicitação digitados por pacientes.
"""

import math
import re
import unicodedata
from typing import Any, Optional

_ESPACOS = re.compile(r"\s+")
_NAO_DIGITOS = re.compile(r"\D+")


def _eh_vazio(valor: Any) -> bool:
    """Indica se o valor é nulo, NaN (pandas) ou string vazia após ``strip``."""
    if valor is None:
        return True
    if isinstance(valor, float) and math.isnan(valor):
        return True
    return isinstance(valor, str) and valor.strip() == ""


def remover_acentos(texto: str) -> str:
    """Remove acentos e diacríticos mantendo os caracteres base (ex: ``ç`` -> ``c``)."""
    decomposto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in decomposto if not unicodedata.combining(c))


def normalizar_texto(valor: Any) -> str:
    """
    Normaliza um texto para comparação: sem acentos, em maiúsculas, com espaços
    internos colapsados e sem espaços nas extremidades. Valores vazios retornam ``""``.

    Exemplo: ``"  Ultrassonografia   de abdômen "`` -> ``"ULTRASSONOGRAFIA DE ABDOMEN"``.
    """
    if _eh_vazio(valor):
        return ""
    texto = remover_acentos(str(valor)).upper()
    return _ESPACOS.sub(" ", texto).strip()


def somente_digitos(valor: Any) -> str:
    """
    Mantém apenas os dígitos de um valor (ex: ``"Nº 890.001"`` -> ``"890001"``).
    Floats inteiros vindos de planilhas (ex: ``890001.0``) são tratados como inteiros.
    """
    if _eh_vazio(valor):
        return ""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    return _NAO_DIGITOS.sub("", str(valor))


def texto_ou_none(valor: Any) -> Optional[str]:
    """Retorna o texto sem espaços nas extremidades, ou ``None`` quando vazio/NaN."""
    if _eh_vazio(valor):
        return None
    return str(valor).strip()
