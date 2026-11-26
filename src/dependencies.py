import os
from typing import Callable
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .providers.interfaces.paciente_provider_interface import PacienteProviderInterface
from .providers.implementations.paciente_postgres_provider import PacientePostgresProvider
from .providers.implementations.paciente_csv_provider import PacienteCsvProvider
from .providers.interfaces.exame_provider_interface import ExameProviderInterface
from .providers.implementations.exame_postgres_provider import ExamePostgresProvider
from .providers.implementations.exame_csv_provider import ExameCsvProvider
from .resources.database import get_aghu_db_session, get_app_db_session
from .providers.interfaces.dashboard_provider_interface import DashboardProviderInterface
from .providers.implementations.dashboard_sqlite_provider import DashboardSqliteProvider
from .providers.interfaces.auditoria_provider_interface import AuditoriaProviderInterface
from .providers.implementations.auditoria_sqlite_provider import AuditoriaSqliteProvider


def get_dashboard_provider(
    session: AsyncSession = Depends(get_app_db_session),
) -> DashboardProviderInterface:
    """Injeta o provedor de indicadores do banco local."""
    return DashboardSqliteProvider(session)


def get_auditoria_provider(
    session: AsyncSession = Depends(get_app_db_session),
) -> AuditoriaProviderInterface:
    """Injeta o provedor somente leitura dos logs de auditoria."""
    return AuditoriaSqliteProvider(session)

# 1. Funções "getter" simples e independentes (privadas por convenção)
def _get_paciente_postgres_provider(
    session: AsyncSession = Depends(get_aghu_db_session)
) -> PacienteProviderInterface:
    return PacientePostgresProvider(session=session)

def _get_paciente_csv_provider() -> PacienteProviderInterface:
    csv_path = os.getenv("PACIENTE_CSV_PATH", "data/pacientes.csv")
    return PacienteCsvProvider(csv_path=csv_path)

def _get_exame_postgres_provider(
    session: AsyncSession = Depends(get_aghu_db_session)
) -> ExameProviderInterface:
    """Instancia o provedor de exames conectado ao PostgreSQL do AGHU."""
    return ExamePostgresProvider(session=session)

def _get_exame_csv_provider() -> ExameProviderInterface:
    """Instancia o provedor de exames baseado no arquivo CSV oficial do AGHU."""
    csv_path = os.getenv("EXAME_CSV_PATH", "data/exames_aghu_mock.csv")
    return ExameCsvProvider(csv_path=csv_path)

# 2. A FÁBRICA: A única função que o roteador vai conhecer.
def get_paciente_provider(strategy: str) -> Callable[..., PacienteProviderInterface]:
    """
    Esta é uma fábrica. Baseado na string 'strategy', ela não retorna o provedor,
    mas sim a FUNÇÃO DE DEPENDÊNCIA correta que o FastAPI deve usar.
    """
    if strategy.upper() == "POSTGRES":
        return _get_paciente_postgres_provider
    elif strategy.upper() == "CSV":
        return _get_paciente_csv_provider
    else:
        raise ValueError(f"Estratégia de provedor desconhecida: {strategy}")


def get_exame_provider(strategy: str) -> Callable[..., ExameProviderInterface]:
    """
    Fábrica de provedor de solicitações de exames (AGHU).
    Baseado na string 'strategy' ('POSTGRES' ou 'CSV'), retorna a função de
    dependência correta que o FastAPI deve usar.
    """
    normalized_strategy = strategy.strip().upper()
    if normalized_strategy == "POSTGRES":
        return _get_exame_postgres_provider
    elif normalized_strategy == "CSV":
        return _get_exame_csv_provider
    else:
        raise ValueError(f"Estratégia de provedor desconhecida: {strategy}")
