"""fix_expense_splits_updated_at

Revision ID: 68f71457720e
Revises: 70404d2ca341
Create Date: 2026-06-09 15:23:58.463562

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '68f71457720e'
down_revision: Union[str, Sequence[str], None] = '70404d2ca341'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column(
        'expense_splits',
        'updated_at',
        existing_type=sa.DateTime(timezone=True),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'expense_splits',
        'updated_at',
        existing_type=sa.DateTime(timezone=True),
        nullable=False,
    )
