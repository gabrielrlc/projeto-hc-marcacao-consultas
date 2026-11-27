"""Cria a tabela de auditoria preservando instalações de desenvolvimento.

Revision ID: e7a011d4b920
Revises: c4f9b2a1e830
"""

from alembic import op
import sqlalchemy as sa

revision = "e7a011d4b920"
down_revision = "c4f9b2a1e830"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Cria a tabela e os índices ausentes, sem modificar logs existentes."""
    inspector = sa.inspect(op.get_bind())
    if not inspector.has_table("audit_logs"):
        op.create_table(
            "audit_logs",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("usuario", sa.String(), nullable=False),
            sa.Column("categoria", sa.String(), nullable=False),
            sa.Column("acao", sa.String(), nullable=False),
            sa.Column("recurso", sa.String(), nullable=False),
            sa.Column("dados_anteriores", sa.Text(), nullable=True),
            sa.Column("dados_novos", sa.Text(), nullable=True),
            sa.Column("ip_origem", sa.String(), nullable=True),
        )
    existing = {index["name"] for index in sa.inspect(op.get_bind()).get_indexes("audit_logs")}
    for column in ("id", "usuario", "categoria", "acao", "recurso"):
        name = f"ix_audit_logs_{column}"
        if name not in existing:
            op.create_index(name, "audit_logs", [column])


def downgrade() -> None:
    """Preserva a tabela: logs são imutáveis, inclusive durante rollback."""
    pass
