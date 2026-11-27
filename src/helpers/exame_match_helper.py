"""
Helper de Correspondência entre Exame do Forms e Exame do AGHU
==============================================================
O paciente informa o exame desejado em texto livre (ou opção de lista) no
Google Forms; o AGHU traz a sigla (``codigo_exame``) e a descrição oficial
(``nome_exame``). Este helper decide se o texto do Forms corresponde a um item
do AGHU de forma tolerante a acentos, caixa, abreviações usuais (USG, RM, TC)
e pequenos erros de digitação.

Regra: o texto corresponde ao item quando é igual à sigla, ou quando **todas**
as palavras significativas do texto do Forms encontram correspondência nas
palavras da descrição do exame (ou da unidade executora ``UDI: ...``).
"""

import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Optional

from .string_helper import normalizar_texto

_NAO_ALFANUMERICO = re.compile(r"[^A-Z0-9]+")

PALAVRAS_IGNORADAS = frozenset(
    {"DE", "DA", "DO", "DAS", "DOS", "COM", "SEM", "E", "EM", "PARA", "O", "A", "EXAME", "EXAMES", "UDI"}
)

# Abreviações/sinônimos usuais digitados por pacientes -> termo presente no AGHU
SINONIMOS: Dict[str, str] = {
    "USG": "ULTRASSONOGRAFIA",
    "US": "ULTRASSONOGRAFIA",
    "ULTRASSOM": "ULTRASSONOGRAFIA",
    "ULTRASOM": "ULTRASSONOGRAFIA",
    "ULTRASSONOGRAFIA": "ULTRASSONOGRAFIA",
    "ECOGRAFIA": "ULTRASSONOGRAFIA",
    "RM": "RESSONANCIA",
    "RNM": "RESSONANCIA",
    "TC": "TOMOGRAFIA",
    "RX": "RADIOGRAFIA",
    "RAIO": "RADIOGRAFIA",
    "ECO": "ECOCARDIOGRAMA",
    "MAMO": "MAMOGRAFIA",
    "DENSITOMETRIA": "DENSITOMETRIA",
    "CINTILOGRAFIA": "CINTILOGRAFIA",
}

SIMILARIDADE_MINIMA = 0.84


def _palavras(texto: Any) -> List[str]:
    """Quebra o texto normalizado em palavras alfanuméricas."""
    return [p for p in _NAO_ALFANUMERICO.sub(" ", normalizar_texto(texto)).split() if p]


def palavras_significativas(texto: Any) -> List[str]:
    """Palavras relevantes do texto do Forms, com sinônimos expandidos."""
    resultado: List[str] = []
    for palavra in _palavras(texto):
        if palavra in SINONIMOS:
            resultado.append(SINONIMOS[palavra])
        elif palavra not in PALAVRAS_IGNORADAS and len(palavra) >= 3:
            resultado.append(palavra)
    return resultado


def _palavras_correspondem(a: str, b: str) -> bool:
    """Compara duas palavras tolerando prefixos e erros de digitação."""
    if a == b:
        return True
    if min(len(a), len(b)) >= 4 and (a.startswith(b) or b.startswith(a)):
        return True
    return min(len(a), len(b)) >= 5 and SequenceMatcher(None, a, b).ratio() >= SIMILARIDADE_MINIMA


def exame_corresponde(texto_forms: Optional[str], item_aghu: Dict[str, Any]) -> bool:
    """Indica se o exame informado no Forms corresponde ao item de exame do AGHU."""
    texto = normalizar_texto(texto_forms)
    if not texto:
        return False
    codigo = normalizar_texto(item_aghu.get("codigo_exame"))
    if codigo and _NAO_ALFANUMERICO.sub("", texto) == _NAO_ALFANUMERICO.sub("", codigo):
        return True

    termos_forms = palavras_significativas(texto)
    if not termos_forms:
        return False

    candidatos = _palavras(item_aghu.get("nome_exame"))
    unidade = normalizar_texto(item_aghu.get("unidade_solicitante"))
    if unidade.startswith("UDI"):
        candidatos += _palavras(unidade)
    candidatos = [c for c in candidatos if c not in PALAVRAS_IGNORADAS]

    return all(any(_palavras_correspondem(t, c) for c in candidatos) for t in termos_forms)
