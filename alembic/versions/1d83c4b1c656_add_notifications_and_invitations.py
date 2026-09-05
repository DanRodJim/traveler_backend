"""add_notifications_and_invitations

Revision ID: 1d83c4b1c656
Revises: a48286de4c1b
Create Date: 2026-09-01 14:28:07.090746

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '1d83c4b1c656'
down_revision: Union[str, Sequence[str], None] = 'a48286de4c1b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'email_notification_preference',
            sa.String(20),
            nullable=False,
            server_default='all'
        )
    )

    op.create_table(
        'notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(30), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.String(500), nullable=False),
        sa.Column('link', sa.String(300), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_notifications_user_id', 'notifications', ['user_id'])
    op.create_index('idx_notifications_user_id_is_read', 'notifications', ['user_id', 'is_read'])

    op.create_table(
        'trip_invitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('trip_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('invited_email', sa.String(255), nullable=False),
        sa.Column('invited_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('token', sa.String(64), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['trip_id'], ['trips.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invited_by'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_trip_invitations_trip_id', 'trip_invitations', ['trip_id'])
    op.create_index('idx_trip_invitations_invited_email', 'trip_invitations', ['invited_email'])
    op.create_index('idx_trip_invitations_token', 'trip_invitations', ['token'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_trip_invitations_token')
    op.drop_index('idx_trip_invitations_invited_email')
    op.drop_index('idx_trip_invitations_trip_id')
    op.drop_table('trip_invitations')

    op.drop_index('idx_notifications_user_id_is_read')
    op.drop_index('idx_notifications_user_id')
    op.drop_table('notifications')

    op.drop_column('users', 'email_notification_preference')
