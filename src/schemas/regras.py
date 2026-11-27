"""
Schemas das Regras Configuráveis (``/api/regras``)
==================================================
Contratos de entrada e saída para Pesos de Prioridade, Regras por Exame e
Matriz de Incompatibilidades, alinhados aos JSON Schemas de
``docs/especificacao/04-modelo-dados.md`` e às interfaces TypeScript de
``docs/especificacao/05-interfaces.md``.

Convenções:
- ``*Create``: corpo do ``POST`` (inclui o código identificador).
- ``*Update``: corpo do ``PUT`` (substituição completa; o código identificador
  de prioridade/exame é imutável e não faz parte do corpo).
- ``*Out``: resposta serializada em camelCase.
"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import Field, field_validator, model_validator

from .base import CamelModel

TipoCriterio = Literal["CLINICA", "GRUPO_CLINICO", "VULNERAVEL", "AFINIDADE_EXAME", "RETORNO_PROXIMO"]
TipoConflito = Literal["MESMO_DIA", "PREPARO", "INTERVALO_MINIMO"]


def _normalizar_codigo(valor: str) -> str:
    """Padroniza códigos identificadores em maiúsculas e sem espaços nas extremidades."""
    return valor.strip().upper()


# ---------------------------------------------------------------------------
# Pesos de Prioridade (regras_prioridade)
# ---------------------------------------------------------------------------


class RegraPrioridadeUpdate(CamelModel):
    """Campos editáveis de uma regra de prioridade (corpo do PUT)."""

    nome: str = Field(min_length=3, max_length=255)
    tipo_criterio: TipoCriterio
    valor_match: str = Field(default="", max_length=255)
    peso: int = Field(ge=0, le=1000)
    ativo: bool = True
    descricao: Optional[str] = Field(default=None, max_length=2000)


class RegraPrioridadeCreate(RegraPrioridadeUpdate):
    """Corpo do POST de uma nova regra de prioridade."""

    codigo: str = Field(min_length=2, max_length=100)

    _codigo_normalizado = field_validator("codigo")(_normalizar_codigo)


class RegraPrioridadeOut(CamelModel):
    """Representação de saída de uma regra de prioridade."""

    id: int
    codigo: str
    nome: str
    tipo_criterio: str
    valor_match: Optional[str]
    peso: int
    ativo: bool
    descricao: Optional[str]
    updated_at: Optional[datetime]


# ---------------------------------------------------------------------------
# Regras por Exame (regras_exames)
# ---------------------------------------------------------------------------


class RegraExameUpdate(CamelModel):
    """Campos editáveis de uma regra de exame (corpo do PUT)."""

    nome_exame: str = Field(min_length=2, max_length=255)
    unidade_executora: Optional[str] = Field(default=None, max_length=255)
    antecedencia_minima_dias: int = Field(default=0, ge=0, le=365)
    janela_retorno_max_horas: Optional[int] = Field(default=None, ge=0, le=8760)
    exige_jejum: bool = False
    priorizar_manha_diabetico: bool = False
    idade_minima_alerta: Optional[int] = Field(default=None, ge=0, le=150)
    orientacoes_preparo: Optional[str] = Field(default=None, max_length=5000)
    ativo: bool = True


class RegraExameCreate(RegraExameUpdate):
    """Corpo do POST de uma nova regra de exame (sigla oficial do AGHU)."""

    codigo_exame: str = Field(min_length=1, max_length=50)

    _codigo_normalizado = field_validator("codigo_exame")(_normalizar_codigo)


class RegraExameOut(CamelModel):
    """Representação de saída de uma regra de exame."""

    id: int
    codigo_exame: str
    nome_exame: str
    unidade_executora: Optional[str]
    antecedencia_minima_dias: int
    janela_retorno_max_horas: Optional[int]
    exige_jejum: bool
    priorizar_manha_diabetico: bool
    idade_minima_alerta: Optional[int]
    orientacoes_preparo: Optional[str]
    ativo: bool
    updated_at: Optional[datetime]


# ---------------------------------------------------------------------------
# Matriz de Incompatibilidades (incompatibilidades_exames)
# ---------------------------------------------------------------------------


class IncompatibilidadeExameIn(CamelModel):
    """Corpo do POST/PUT de um par de exames incompatíveis."""

    codigo_exame_origem: str = Field(min_length=1, max_length=50)
    codigo_exame_conflitante: str = Field(min_length=1, max_length=50)
    tipo_conflito: TipoConflito
    intervalo_minimo_dias: int = Field(default=0, ge=0, le=365)
    motivo: str = Field(min_length=3, max_length=2000)
    ativo: bool = True

    _codigos_normalizados = field_validator(
        "codigo_exame_origem", "codigo_exame_conflitante"
    )(_normalizar_codigo)

    @model_validator(mode="after")
    def _validar_par(self) -> "IncompatibilidadeExameIn":
        """Impede par de um exame consigo mesmo e intervalo nulo em INTERVALO_MINIMO."""
        if self.codigo_exame_origem == self.codigo_exame_conflitante:
            raise ValueError("O exame conflitante deve ser diferente do exame de origem.")
        if self.tipo_conflito == "INTERVALO_MINIMO" and self.intervalo_minimo_dias < 1:
            raise ValueError("Conflitos do tipo INTERVALO_MINIMO exigem intervaloMinimoDias >= 1.")
        return self


class IncompatibilidadeExameOut(CamelModel):
    """Representação de saída de um par de exames incompatíveis."""

    id: int
    codigo_exame_origem: str
    codigo_exame_conflitante: str
    tipo_conflito: str
    intervalo_minimo_dias: int
    motivo: str
    ativo: bool
