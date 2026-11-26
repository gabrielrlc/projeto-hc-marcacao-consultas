"""Migração da auditoria em instalações novas e preexistentes."""

from datetime import datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, select

from src.models import AuditLog


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
