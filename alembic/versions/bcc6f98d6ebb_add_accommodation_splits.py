"""add_accommodation_splits

Revision ID: bcc6f98d6ebb
Revises: f03498165ee6
Create Date: 2026-08-20 13:49:39.494798

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'bcc6f98d6ebb'
down_revision: Union[str, Sequence[str], None] = 'f03498165ee6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'accommodations',
        sa.Column('paid_by', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_accommodations_paid_by_users',
        'accommodations', 'users',
        ['paid_by'], ['id'],
    )
    op.add_column(
        'accommodations',
        sa.Column('is_private', sa.Boolean(), nullable=False, server_default='true')
    )

    op.create_table(
        'accommodation_splits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('accommodation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('is_paid', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['accommodation_id'], ['accommodations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_accommodation_splits_accommodation_id', 'accommodation_splits', ['accommodation_id'])
    op.create_index('idx_accommodation_splits_user_id', 'accommodation_splits', ['user_id'])



def downgrade() -> None:
    op.drop_index('idx_accommodation_splits_user_id')
    op.drop_index('idx_accommodation_splits_accommodation_id')
    op.drop_table('accommodation_splits')
    op.drop_column('accommodations', 'is_private')
    op.drop_constraint('fk_accommodations_paid_by_users', 'accommodations', type_='foreignkey')
    op.drop_column('accommodations', 'paid_by')
