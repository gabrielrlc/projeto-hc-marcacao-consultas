"""
Helper de Classificação Geográfica Operacional
==============================================
Deriva a ``regiao_geografica`` (``CAPITAL`` | ``RMR`` | ``INTERIOR`` |
``NAO_INFORMADO``) a partir do município informado pelo paciente. É usada
apenas pelo filtro operacional de vagas de última hora e **não** altera o
score de prioridade clínica.

A composição da Região Metropolitana do Recife segue a Lei Complementar
Estadual nº 10/1994 e alterações (inclusão de Goiana em 2018). Trata-se de
dado geográfico de referência, não de regra clínica configurável.
"""

from typing import Any, Optional

from .string_helper import normalizar_texto

CAPITAL = "RECIFE"

MUNICIPIOS_RMR: frozenset[str] = frozenset(
    {
        "ABREU E LIMA",
        "ARACOIABA",
        "CABO DE SANTO AGOSTINHO",
        "CAMARAGIBE",
        "GOIANA",
        "IGARASSU",
        "ILHA DE ITAMARACA",
        "IPOJUCA",
        "ITAPISSUMA",
        "JABOATAO DOS GUARARAPES",
        "MORENO",
        "OLINDA",
        "PAULISTA",
        "SAO LOURENCO DA MATA",
    }
)

# Formas abreviadas usuais digitadas no Forms -> nome oficial
_APELIDOS_MUNICIPIOS: dict[str, str] = {
    "JABOATAO": "JABOATAO DOS GUARARAPES",
    "CABO": "CABO DE SANTO AGOSTINHO",
    "ITAMARACA": "ILHA DE ITAMARACA",
    "SAO LOURENCO": "SAO LOURENCO DA MATA",
}

_SUFIXOS_UF = (" PE", " - PE", "/PE", "-PE")


def normalizar_municipio(municipio: Any) -> str:
    """Normaliza o nome do município (sem acentos, maiúsculas, sem sufixo ``/PE``)."""
    nome = normalizar_texto(municipio)
    for sufixo in _SUFIXOS_UF:
        if nome.endswith(sufixo):
            nome = nome[: -len(sufixo)].strip(" -/")
            break
    return _APELIDOS_MUNICIPIOS.get(nome, nome)


def classificar_regiao(municipio: Optional[Any]) -> str:
    """Classifica o município em ``CAPITAL``, ``RMR``, ``INTERIOR`` ou ``NAO_INFORMADO``."""
    nome = normalizar_municipio(municipio)
    if not nome:
        return "NAO_INFORMADO"
    if nome == CAPITAL:
        return "CAPITAL"
    if nome in MUNICIPIOS_RMR:
        return "RMR"
    return "INTERIOR"
