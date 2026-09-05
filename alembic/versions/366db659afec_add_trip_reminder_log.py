"""add_trip_reminder_log

Revision ID: 366db659afec
Revises: cfec470f5a57
Create Date: 2026-09-05 15:37:03.284203

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '366db659afec'
down_revision: Union[str, Sequence[str], None] = 'cfec470f5a57'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'trip_reminder_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('trip_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('days_before', sa.Integer(), nullable=False),
        sa.Column('sent_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('trip_id', 'user_id', 'days_before', name='uq_trip_reminder_once'),
    )
    op.create_index('idx_trip_reminder_logs_trip_user', 'trip_reminder_logs', ['trip_id', 'user_id'])



def downgrade() -> None:
    op.drop_index('idx_trip_reminder_logs_trip_user')
    op.drop_table('trip_reminder_logs')
