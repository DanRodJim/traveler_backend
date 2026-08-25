"""add_personal_budget_to_trip_members

Revision ID: 84b008360fba
Revises: b60e531d49cb
Create Date: 2026-07-28 14:32:15.052104

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '84b008360fba'
down_revision: Union[str, Sequence[str], None] = 'b60e531d49cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'trip_members',
        sa.Column('personal_budget', sa.Numeric(12, 2), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('trip_members', 'personal_budget')
