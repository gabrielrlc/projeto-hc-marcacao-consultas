"""Regras e contrato dos indicadores operacionais."""

from datetime import datetime, timezone

from ..helpers.datetime_helper import utc_sem_fuso, validar_periodo
from ..providers.interfaces.dashboard_provider_interface import DashboardProviderInterface
from ..schemas.dashboard import KpiDashboard


async def obter_kpis(
    provider: DashboardProviderInterface,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
    codigo_exame: str | None = None,
) -> KpiDashboard:
    """Valida filtros e usa um único instante UTC para todos os indicadores."""
    inicio, fim = validar_periodo(data_inicio, data_fim)
    agora = utc_sem_fuso(datetime.now(timezone.utc))
    resultado = await provider.obter_kpis(agora, inicio, fim, codigo_exame)
    resultado["tempo_medio_espera_dias"] = round(resultado["tempo_medio_espera_dias"], 2)
    return KpiDashboard.model_validate(resultado)
