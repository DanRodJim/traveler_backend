"""add_expense_splits

Revision ID: 70404d2ca341
Revises: 0ef0f9077be9
Create Date: 2026-05-18 15:02:30.274655

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '70404d2ca341'
down_revision: Union[str, Sequence[str], None] = '0ef0f9077be9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_column('expenses', 'split_between')
    
    op.create_foreign_key(
        'fk_expenses_paid_by_users',
        'expenses', 'users',
        ['paid_by'], ['id'],
        ondelete='CASCADE'
    )
    
    op.create_table(
        'expense_splits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('expense_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['expense_id'], ['expenses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    op.create_index('idx_expense_splits_expense_id', 'expense_splits', ['expense_id'])
    op.create_index('idx_expense_splits_user_id', 'expense_splits', ['user_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_expense_splits_user_id')
    op.drop_index('idx_expense_splits_expense_id')
    op.drop_table('expense_splits')
    op.drop_constraint('fk_expenses_paid_by_users', 'expenses', type_='foreignkey')
    op.drop_column('expenses', 'paid_by')
    op.add_column(
        'expenses', 
        sa.Column('split_between', postgresql.JSON(), nullable=True)
    )