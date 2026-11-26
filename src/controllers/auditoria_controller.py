"""Validação e serialização das consultas de auditoria."""

from datetime import datetime, timezone
import json

from fastapi import HTTPException

from ..helpers.datetime_helper import validar_periodo
from ..providers.interfaces.auditoria_provider_interface import AuditoriaProviderInterface
from ..schemas.auditoria import AuditLogPage


async def listar_logs(
    provider: AuditoriaProviderInterface,
    categoria: str | None = None,
    usuario: str | None = None,
    data_inicio: datetime | None = None,
    data_fim: datetime | None = None,
    page: int = 1,
    page_size: int = 50,
) -> AuditLogPage:
    """Valida o período e devolve JSON estruturado sem modificar os eventos."""
    inicio, fim = validar_periodo(data_inicio, data_fim)
    items, total = await provider.listar_logs(categoria, usuario, inicio, fim, page, page_size)
    for item in items:
        item["created_at"] = item["created_at"].replace(tzinfo=timezone.utc)
        for campo in ("dados_anteriores", "dados_novos"):
            try:
                item[campo] = json.loads(item[campo]) if item[campo] is not None else None
            except json.JSONDecodeError as exc:
                raise HTTPException(status_code=500, detail="Registro de auditoria contém JSON inválido.") from exc
    return AuditLogPage(items=items, total=total, page=page, page_size=page_size)
