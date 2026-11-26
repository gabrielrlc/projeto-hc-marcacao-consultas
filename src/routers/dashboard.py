"""Endpoints administrativos de indicadores da Central."""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ..auth.auth import auth_handler
from ..controllers import dashboard_controller
from ..dependencies import get_dashboard_provider
from ..providers.interfaces.dashboard_provider_interface import DashboardProviderInterface
from ..schemas.dashboard import KpiDashboard
from .admin import verify_admin_group

router = APIRouter(
    prefix="/api/dashboard",
    tags=["Dashboard"],
    dependencies=[Depends(auth_handler.decode_token), Depends(verify_admin_group)],
)


@router.get("/kpis", response_model=KpiDashboard)
async def obter_kpis(
    provider: Annotated[DashboardProviderInterface, Depends(get_dashboard_provider)],
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
    codigo_exame: Annotated[str | None, Query(min_length=1)] = None,
) -> KpiDashboard:
    """Consulta KPIs; o período inclusivo filtra a entrada dos itens na fila (UTC)."""
    return await dashboard_controller.obter_kpis(provider, data_inicio, data_fim, codigo_exame)
