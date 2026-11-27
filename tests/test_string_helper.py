"""Testes do helper de normalização de textos (``src/helpers/string_helper.py``)."""

import math

import pytest

from src.helpers.string_helper import (
    normalizar_texto,
    remover_acentos,
    somente_digitos,
    texto_ou_none,
)


def test_remover_acentos() -> None:
    """Remove diacríticos preservando os caracteres base."""
    assert remover_acentos("Ressonância Magnética — Coração") == "Ressonancia Magnetica — Coracao"


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("  Ultrassonografia   de abdômen ", "ULTRASSONOGRAFIA DE ABDOMEN"),
        ("São Lourenço da Mata", "SAO LOURENCO DA MATA"),
        ("USAX", "USAX"),
        (123, "123"),
        (None, ""),
        ("   ", ""),
        (math.nan, ""),
    ],
)
def test_normalizar_texto(entrada, esperado) -> None:
    """Normaliza acentos, caixa e espaços; vazios viram string vazia."""
    assert normalizar_texto(entrada) == esperado


@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("Nº 890.001", "890001"),
        (" 890001 ", "890001"),
        (890001, "890001"),
        (890001.0, "890001"),
        ("sem numero", ""),
        (None, ""),
        (math.nan, ""),
    ],
)
def test_somente_digitos(entrada, esperado) -> None:
    """Extrai apenas dígitos, tratando floats inteiros de planilhas."""
    assert somente_digitos(entrada) == esperado


@pytest.mark.parametrize(
    "entrada, esperado",
    [(" Recife ", "Recife"), ("", None), ("  ", None), (None, None), (math.nan, None), (0, "0")],
)
def test_texto_ou_none(entrada, esperado) -> None:
    """Retorna texto limpo ou None para valores vazios/NaN."""
    assert texto_ou_none(entrada) == esperado
