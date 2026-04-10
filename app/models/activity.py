from __future__ import annotations

from sqlalchemy import String, Date, Time, Numeric, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.db import Base

from typing import Optional, TYPE_CHECKING
from datetime import datetime, date, time
from decimal import Decimal
from app.common.types import ActivityCategory
import uuid

if TYPE_CHECKING:
    from app.models.trip import Trip


class Activity(Base):
    __tablename__ = "activities"

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

    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    activity_date: Mapped[date] = mapped_column(Date, nullable=False)

    start_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    end_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    category: Mapped[ActivityCategory] = mapped_column(
        SQLEnum(ActivityCategory, name="activity_category"),
        default=ActivityCategory.other
    )

    cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now()
    )

    # Relationships
    trip: Mapped[Trip] = relationship(
        "Trip",
        back_populates="activities"
    )