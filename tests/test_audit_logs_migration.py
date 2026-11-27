"""Migração da auditoria em instalações novas e preexistentes."""

from datetime import datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, select, text

from src.models import AcompanhamentoFila, AuditLog


@pytest.mark.parametrize("preexistente", [False, True])
def test_migracao_auditoria_preserva_eventos(tmp_path: Path, preexistente: bool) -> None:
    """Cria o schema e preserva eventos no upgrade, downgrade e reupgrade."""
    root = Path(__file__).resolve().parent.parent
    engine = create_engine(f"sqlite:///{tmp_path / 'audit_migration.db'}")
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", str(engine.url))
    table = AuditLog.__table__
    try:
        if preexistente:
            table.create(engine)
            with engine.begin() as conn:
                conn.execute(table.insert().values(
                    created_at=datetime(2026, 11, 26), usuario="admin.teste",
                    categoria="CONFIGURACAO", acao="ALTERAR_REGRA", recurso="regra:1",
                    dados_novos='{"peso": 80}',
                ))
        command.upgrade(cfg, "head")
        inspector = inspect(engine)
        assert {col["name"] for col in inspector.get_columns("audit_logs")} == set(table.columns.keys())
        assert {idx["name"] for idx in inspector.get_indexes("audit_logs")} == {idx.name for idx in table.indexes}
        if not preexistente:
            with engine.begin() as conn:
                conn.execute(table.insert().values(
                    created_at=datetime(2026, 11, 26), usuario="admin.teste",
                    categoria="CONFIGURACAO", acao="ALTERAR_REGRA", recurso="regra:1",
                    dados_novos='{"peso": 80}',
                ))
        with engine.connect() as conn:
            antes = [dict(row) for row in conn.execute(select(table)).mappings()]
        assert len(antes) == 1
        command.downgrade(cfg, "c4f9b2a1e830")
        assert inspect(engine).has_table("audit_logs")
        command.upgrade(cfg, "head")
        with engine.connect() as conn:
            depois = [dict(row) for row in conn.execute(select(table)).mappings()]
        assert antes == depois
    finally:
        engine.dispose()


@pytest.mark.parametrize("revisao_origem", ["e7a011d4b920", "d7e3a9c41f02"])
def test_upgrade_unifica_auditoria_e_idade_preservando_dados(
    tmp_path: Path, revisao_origem: str
) -> None:
    """Atualiza instalações em qualquer ponta sem perder a fila ou a auditoria."""
    root = Path(__file__).resolve().parent.parent
    engine = create_engine(f"sqlite:///{tmp_path / 'merge_migrations.db'}")
    cfg = Config(str(root / "alembic.ini"))
    cfg.set_main_option("script_location", str(root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", str(engine.url))
    try:
        command.upgrade(cfg, revisao_origem)
        tem_idade = revisao_origem == "d7e3a9c41f02"
        with engine.begin() as conn:
            valores: dict[str, object] = {
                "codigo_solicitacao": "SOL-INTEGRACAO",
                "nome_paciente": "PACIENTE SINTETICO",
            }
            if tem_idade:
                valores["idade_informada"] = 67
            conn.execute(AcompanhamentoFila.__table__.insert().values(**valores))
            if not tem_idade:
                conn.execute(AuditLog.__table__.insert().values(
                    usuario="admin.teste", categoria="NEGOCIO_CLINICO",
                    acao="IMPORTAR_FORMS", recurso="importacao:1",
                    dados_novos='{"total": 1}',
                ))

        command.upgrade(cfg, "head")

        inspector = inspect(engine)
        assert inspector.has_table("audit_logs")
        assert "idade_informada" in {
            column["name"] for column in inspector.get_columns("acompanhamento_fila")
        }
        with engine.connect() as conn:
            assert conn.execute(text("SELECT version_num FROM alembic_version")).scalars().all() == ["f011d7e3a901"]
            item = conn.execute(select(AcompanhamentoFila.__table__)).mappings().one()
            assert item["codigo_solicitacao"] == "SOL-INTEGRACAO"
            assert item["idade_informada"] == (67 if tem_idade else None)
            logs = conn.execute(select(AuditLog.__table__)).mappings().all()
            assert len(logs) == (0 if tem_idade else 1)
            if logs:
                assert logs[0]["dados_novos"] == '{"total": 1}'
    finally:
        engine.dispose()
