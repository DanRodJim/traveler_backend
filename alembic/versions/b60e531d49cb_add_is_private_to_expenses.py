"""add_is_private_to_expenses

Revision ID: b60e531d49cb
Revises: 118d1d3d854a
Create Date: 2026-07-18 18:13:55.160506

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b60e531d49cb'
down_revision: Union[str, Sequence[str], None] = '118d1d3d854a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'expenses',
        sa.Column(
            'is_private',
            sa.Boolean(),
            nullable=False,
            server_default='true'
        )
    )


def downgrade() -> None:
    op.drop_column('expenses', 'is_private')
