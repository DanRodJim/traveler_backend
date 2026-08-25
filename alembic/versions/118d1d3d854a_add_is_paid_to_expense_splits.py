"""add_is_paid_to_expense_splits

Revision ID: 118d1d3d854a
Revises: 68f71457720e
Create Date: 2026-06-15 15:35:34.155627

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '118d1d3d854a'
down_revision: Union[str, Sequence[str], None] = '68f71457720e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'expense_splits',
        sa.Column('is_paid', sa.Boolean(), nullable=False, server_default='false')
    )
    op.add_column(
        'expense_splits',
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('expense_splits', 'paid_at')
    op.drop_column('expense_splits', 'is_paid')
