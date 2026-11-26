"""Agregações SQLAlchemy dos indicadores no SQLite local."""

from datetime import datetime
from typing import Any

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.acompanhamento_fila import AcompanhamentoFila
from ..interfaces.dashboard_provider_interface import DashboardProviderInterface


class DashboardSqliteProvider(DashboardProviderInterface):
    """Consulta apenas agregados, sem carregar dados pessoais dos pacientes."""

    def __init__(self, session: AsyncSession) -> None:
        """Recebe a sessão do banco local por injeção de dependência."""
        self.session = session

    async def obter_kpis(
        self,
        agora: datetime,
        data_inicio: datetime | None = None,
        data_fim: datetime | None = None,
        codigo_exame: str | None = None,
    ) -> dict[str, Any]:
        """Calcula os nove indicadores com os mesmos filtros e instante UTC."""
        fila = AcompanhamentoFila
        filtros = [fila.deleted_at.is_(None)]
        if data_inicio is not None:
            filtros.append(fila.created_at >= data_inicio)
        if data_fim is not None:
            filtros.append(fila.created_at <= data_fim)
        if codigo_exame is not None:
            filtros.append(fila.codigo_exame == codigo_exame)

        valida = fila.status_higienizacao == "VALIDA"
        na_fila = and_(valida, fila.status_operacional == "NA_FILA")
        aguardando = and_(valida, fila.status_operacional == "AGUARDANDO_CONFIRMACAO_24H")
        criterios = {
            "total_na_fila": na_fila,
            "aguardando_24h": aguardando,
            "prazo_24h_vencidos": and_(aguardando, fila.prazo_confirmacao_em <= agora),
            "confirmados_agendados": and_(valida, fila.status_operacional == "CONFIRMADO_AGENDADO_AGHU"),
            "duplicidades_barradas": fila.status_higienizacao == "DUPLICADA",
            "divergencias_detectadas": fila.status_higienizacao == "DIVERGENCIA_EXAME",
        }
        contagens = [
            func.coalesce(func.sum(case((criterio, 1), else_=0)), 0).label(nome)
            for nome, criterio in criterios.items()
        ]
        dias_espera = case(
            (fila.created_at <= agora, func.julianday(agora) - func.julianday(fila.created_at)),
            else_=0.0,
        )
        media = func.coalesce(func.avg(case((na_fila, dias_espera))), 0.0)
        resumo = await self.session.execute(
            select(*contagens, media.label("tempo_medio_espera_dias")).where(*filtros)
        )
        resultado = dict(resumo.mappings().one())

        exame = func.coalesce(func.nullif(fila.codigo_exame, ""), "NAO_INFORMADO")
        regiao = fila.regiao_geografica
        quantidade = func.count().label("quantidade")
        for chave, identificador, coluna in (
            ("fila_por_exame", "exame", exame),
            ("fila_por_regiao", "regiao", regiao),
        ):
            consulta = (
                select(coluna.label(identificador), quantidade)
                .where(*filtros, na_fila)
                .group_by(coluna)
                .order_by(quantidade.desc(), coluna.asc())
            )
            grupos = await self.session.execute(consulta)
            resultado[chave] = [dict(row) for row in grupos.mappings()]
        return resultado
