"""Une as revisões publicadas de auditoria e idade informada.

Revision ID: f011d7e3a901
Revises: e7a011d4b920, d7e3a9c41f02

As alterações de schema pertencem às revisões originais. Esta revisão apenas
reúne as duas pontas para permitir ``alembic upgrade head`` em qualquer origem.
"""

revision = "f011d7e3a901"
down_revision = ("e7a011d4b920", "d7e3a9c41f02")
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Une os históricos depois de aplicar ambas as revisões originais."""
    pass


def downgrade() -> None:
    """Retorna às duas pontas sem alterar tabelas ou registros."""
    pass
