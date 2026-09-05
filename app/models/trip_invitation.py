from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, String, Enum as SQLEnum, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.db import Base

from typing import Optional, TYPE_CHECKING
from datetime import datetime
from app.common.types import MemberRole, InvitationStatus
import uuid

if TYPE_CHECKING:
    from app.models.trip import Trip
    from app.models.user import User


class TripInvitation(Base):
    __tablename__ = "trip_invitations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    invited_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    invited_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    role: Mapped[MemberRole] = mapped_column(
        SQLEnum(
            *[role.value for role in MemberRole],
            name='member_role'
        ),
        nullable=False
    )

    status: Mapped[InvitationStatus] = mapped_column(
        SQLEnum(
            *[s.value for s in InvitationStatus],
            name='invitation_status'
        ),
        nullable=False,
        default=InvitationStatus.PENDING.value
    )

    token: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    trip: Mapped["Trip"] = relationship("Trip")
    inviter: Mapped["User"] = relationship("User", foreign_keys=[invited_by])