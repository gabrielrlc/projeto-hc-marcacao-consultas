"""Consulta paginada da tabela append-only audit_logs."""

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.audit_log import AuditLog
from ..interfaces.auditoria_provider_interface import AuditoriaProviderInterface


class AuditoriaSqliteProvider(AuditoriaProviderInterface):
    """Oferece somente operações SELECT sobre os logs."""

    def __init__(self, session: AsyncSession) -> None:
        """Recebe a sessão SQLite da aplicação."""
        self.session = session

    async def listar_logs(
        self,
        categoria: str | None = None,
        usuario: str | None = None,
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[dict[str, Any]], int]:
        """Combina filtros exatos com AND e ordena data e ID decrescentes."""
        filtros = []
        if categoria is not None:
            filtros.append(AuditLog.categoria == categoria)
        if usuario is not None:
            filtros.append(AuditLog.usuario == usuario)
        if data_inicio is not None:
            filtros.append(AuditLog.created_at >= data_inicio)
        if data_fim is not None:
            filtros.append(AuditLog.created_at <= data_fim)
        total = await self.session.scalar(select(func.count()).select_from(AuditLog).where(*filtros))
        result = await self.session.execute(
            select(AuditLog.__table__)
            .where(*filtros)
            .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return [dict(row) for row in result.mappings()], int(total or 0)
