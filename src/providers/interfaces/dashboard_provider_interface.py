"""Contrato de leitura dos indicadores operacionais."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class DashboardProviderInterface(ABC):
    """Desacopla os indicadores da fonte de persistência."""

    @abstractmethod
    async def obter_kpis(
        self,
        agora: datetime,
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
        codigo_exame: str | None = None,
    ) -> dict[str, Any]:
        """Retorna agregados dos itens não excluídos, aplicando todos os filtros."""
