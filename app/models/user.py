from __future__ import annotations

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.db import Base
from datetime import datetime
from typing import List, TYPE_CHECKING, Optional
import uuid

if TYPE_CHECKING:
    from app.models.trip import Trip, TripMember


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now()
    )

    # Relationships
    owned_trips: Mapped[List[Trip]] = relationship(
        "Trip",
        back_populates="owner",
        foreign_keys="Trip.owner_id"
    )
    trip_memberships: Mapped[List[TripMember]] = relationship(
        "TripMember",
        back_populates="user"
    )