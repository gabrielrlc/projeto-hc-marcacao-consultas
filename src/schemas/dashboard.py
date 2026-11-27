"""Contrato público dos nove indicadores do dashboard."""

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class FilaPorExame(BaseModel):
    """Quantidade de itens na fila para um código de exame."""

    exame: str
    quantidade: int


class FilaPorRegiao(BaseModel):
    """Quantidade de itens na fila para uma região."""

    regiao: str
    quantidade: int


class KpiDashboard(BaseModel):
    """Serializa em camelCase o contrato IKpiDashboard do frontend."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    total_na_fila: int
    aguardando_24h: int = Field(serialization_alias="aguardando24h")
    prazo_24h_vencidos: int = Field(serialization_alias="prazo24hVencidos")
    confirmados_agendados: int
    duplicidades_barradas: int
    divergencias_detectadas: int
    tempo_medio_espera_dias: float
    fila_por_exame: list[FilaPorExame]
    fila_por_regiao: list[FilaPorRegiao]
