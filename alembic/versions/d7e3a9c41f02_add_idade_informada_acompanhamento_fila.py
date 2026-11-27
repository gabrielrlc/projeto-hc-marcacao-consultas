"""add idade_informada to acompanhamento_fila

Revision ID: d7e3a9c41f02
Revises: c4f9b2a1e830
Create Date: 2026-11-27 10:00:00.000000

Adiciona a coluna ``idade_informada`` (idade declarada pelo paciente no Google
Forms) à tabela ``acompanhamento_fila``. Usada pelo motor de priorização
(vulneráveis: crianças/idosos) e pelo alerta etário de mamografia enquanto o
SQL do AGHU não expõe ``data_nascimento``.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d7e3a9c41f02"
down_revision: Union[str, Sequence[str], None] = "c4f9b2a1e830"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona a coluna anulável ``idade_informada``."""
    with op.batch_alter_table("acompanhamento_fila") as batch_op:
        batch_op.add_column(sa.Column("idade_informada", sa.Integer(), nullable=True))


def downgrade() -> None:
    """Remove a coluna ``idade_informada``."""
    with op.batch_alter_table("acompanhamento_fila") as batch_op:
        batch_op.drop_column("idade_informada")
