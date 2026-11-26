"""Contratos de consulta somente leitura dos logs de auditoria."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, JsonValue

CategoriaAuditoria = Literal["SEGURANCA", "NEGOCIO_CLINICO", "CONFIGURACAO"]


class AuditLogResponse(BaseModel):
    """Evento com seus estados anterior e novo desserializados."""

    id: int
    created_at: datetime
    usuario: str
    categoria: str
    acao: str
    recurso: str
    dados_anteriores: JsonValue
    dados_novos: JsonValue
    ip_origem: str | None


class AuditLogPage(BaseModel):
    """Página de eventos e total correspondente aos filtros."""

    items: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
