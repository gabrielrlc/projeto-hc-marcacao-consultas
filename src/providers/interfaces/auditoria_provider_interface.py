"""Contrato de leitura imutável da auditoria."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class AuditoriaProviderInterface(ABC):
    """Desacopla a consulta de auditoria do banco local."""

    @abstractmethod
    async def listar_logs(
        self,
        categoria: str | None = None,
        usuario: str | None = None,
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[dict[str, Any]], int]:
        """Retorna uma página ordenada e o total dos registros filtrados."""
