"""add_coordinates_to_activities_and_accommodations

Revision ID: a48286de4c1b
Revises: 0c1e5245c064
Create Date: 2026-08-25 14:28:15.402171

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a48286de4c1b'
down_revision: Union[str, Sequence[str], None] = '0c1e5245c064'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('activities', sa.Column('latitude', sa.Numeric(9, 6), nullable=True))
    op.add_column('activities', sa.Column('longitude', sa.Numeric(9, 6), nullable=True))
    op.add_column('accommodations', sa.Column('latitude', sa.Numeric(9, 6), nullable=True))
    op.add_column('accommodations', sa.Column('longitude', sa.Numeric(9, 6), nullable=True))


def downgrade() -> None:
    op.drop_column('accommodations', 'longitude')
    op.drop_column('accommodations', 'latitude')
    op.drop_column('activities', 'longitude')
    op.drop_column('activities', 'latitude')
