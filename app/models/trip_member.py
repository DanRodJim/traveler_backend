from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.db import Base

from typing import TYPE_CHECKING
from app.common.types import MemberRole
from datetime import datetime
import uuid

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.trip import Trip

class TripMember(Base):
    __tablename__ = "trip_members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("trips.id"),
        nullable=False,
        index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    role: Mapped[MemberRole] = mapped_column(
        SQLEnum(
            *[role.value for role in MemberRole],
            name='member_role'
        ),
        nullable=False
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    # Relationships
    trip: Mapped[Trip] = relationship(
        "Trip",
        back_populates="members"
    )
    user: Mapped[User] = relationship(
        "User",
        back_populates="trip_memberships"
    )