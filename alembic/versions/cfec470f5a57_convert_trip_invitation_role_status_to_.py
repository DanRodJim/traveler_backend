"""convert_trip_invitation_role_status_to_enum

Revision ID: cfec470f5a57
Revises: 1d83c4b1c656
Create Date: 2026-09-03 00:12:33.749779

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'cfec470f5a57'
down_revision: Union[str, Sequence[str], None] = '1d83c4b1c656'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    invitation_status_enum = postgresql.ENUM(
        'pending', 'accepted', 'declined', 'expired', name='invitation_status'
    )
    invitation_status_enum.create(op.get_bind())

    op.execute(
        "ALTER TABLE trip_invitations "
        "ALTER COLUMN role TYPE member_role "
        "USING role::member_role"
    )

    op.execute("ALTER TABLE trip_invitations ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "ALTER TABLE trip_invitations "
        "ALTER COLUMN status TYPE invitation_status "
        "USING status::invitation_status"
    )
    op.execute(
        "ALTER TABLE trip_invitations "
        "ALTER COLUMN status SET DEFAULT 'pending'::invitation_status"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE trip_invitations ALTER COLUMN status DROP DEFAULT")
    op.execute(
        "ALTER TABLE trip_invitations "
        "ALTER COLUMN status TYPE VARCHAR(20) "
        "USING status::text"
    )
    op.execute(
        "ALTER TABLE trip_invitations "
        "ALTER COLUMN status SET DEFAULT 'pending'"
    )

    op.execute(
        "ALTER TABLE trip_invitations "
        "ALTER COLUMN role TYPE VARCHAR(20) "
        "USING role::text"
    )

    op.execute("DROP TYPE invitation_status")
