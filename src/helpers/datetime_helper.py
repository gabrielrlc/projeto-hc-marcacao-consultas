"""Normalização das datas de consulta para UTC no SQLite."""

from datetime import datetime, timezone

from fastapi import HTTPException


def utc_sem_fuso(value: datetime) -> datetime:
    """Converte para UTC sem tzinfo; datas sem offset são interpretadas como UTC."""
    aware = value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)
    return aware.astimezone(timezone.utc).replace(tzinfo=None)


def validar_periodo(
    data_inicio: datetime | None, data_fim: datetime | None
) -> tuple[datetime | None, datetime | None]:
    """Normaliza o intervalo inclusivo e rejeita início posterior ao fim."""
    inicio = utc_sem_fuso(data_inicio) if data_inicio is not None else None
    fim = utc_sem_fuso(data_fim) if data_fim is not None else None
    if inicio is not None and fim is not None and inicio > fim:
        raise HTTPException(status_code=400, detail="data_inicio deve ser anterior ou igual a data_fim.")
    return inicio, fim
