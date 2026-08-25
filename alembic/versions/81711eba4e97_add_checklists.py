"""add_checklists

Revision ID: 81711eba4e97
Revises: 84b008360fba
Create Date: 2026-08-05 23:31:08.725910

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '81711eba4e97'
down_revision: Union[str, Sequence[str], None] = '84b008360fba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'checklist_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('trip_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('list_type', sa.String(20), nullable=False),  # 'tasks' | 'packing'
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_private', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_checklist_items_trip_id', 'checklist_items', ['trip_id'])
    op.create_index('idx_checklist_items_created_by', 'checklist_items', ['created_by'])


def downgrade() -> None:
    op.drop_index('idx_checklist_items_created_by')
    op.drop_index('idx_checklist_items_trip_id')
    op.drop_table('checklist_items')
