"""add_activity_splits

Revision ID: 0c1e5245c064
Revises: bcc6f98d6ebb
Create Date: 2026-08-21 10:14:32.285844

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '0c1e5245c064'
down_revision: Union[str, Sequence[str], None] = 'bcc6f98d6ebb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'activities',
        sa.Column('paid_by', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.create_foreign_key(
        'fk_activities_paid_by_users',
        'activities', 'users',
        ['paid_by'], ['id'],
    )
    op.add_column(
        'activities',
        sa.Column('is_private', sa.Boolean(), nullable=False, server_default='true')
    )

    op.create_table(
        'activity_splits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('activity_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(12, 2), nullable=False),
        sa.Column('is_paid', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('paid_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['activity_id'], ['activities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_activity_splits_activity_id', 'activity_splits', ['activity_id'])
    op.create_index('idx_activity_splits_user_id', 'activity_splits', ['user_id'])


def downgrade() -> None:
    op.drop_index('idx_activity_splits_user_id')
    op.drop_index('idx_activity_splits_activity_id')
    op.drop_table('activity_splits')
    op.drop_column('activities', 'is_private')
    op.drop_constraint('fk_activities_paid_by_users', 'activities', type_='foreignkey')
    op.drop_column('activities', 'paid_by')
