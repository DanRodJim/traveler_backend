"""add_flight_splits

Revision ID: f03498165ee6
Revises: 81711eba4e97
Create Date: 2026-08-18 15:21:57.003166

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f03498165ee6'
down_revision: Union[str, Sequence[str], None] = '81711eba4e97'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'flights',
        sa.Column('paid_by', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_flights_paid_by_users',
        'flights', 'users',
        ['paid_by'], ['id'],
    )
    op.add_column(
        'flights',
        sa.Column('is_private', sa.Boolean(), nullable=False, server_default='true')
    )

    op.create_table(
        'flight_splits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('flight_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('is_paid', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['flight_id'], ['flights.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_flight_splits_flight_id', 'flight_splits', ['flight_id'])
    op.create_index('idx_flight_splits_user_id', 'flight_splits', ['user_id'])



def downgrade() -> None:
    op.drop_index('idx_flight_splits_user_id')
    op.drop_index('idx_flight_splits_flight_id')
    op.drop_table('flight_splits')
    op.drop_column('flights', 'is_private')
    op.drop_constraint('fk_flights_paid_by_users', 'flights', type_='foreignkey')
    op.drop_column('flights', 'paid_by')
