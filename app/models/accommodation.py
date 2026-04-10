from __future__ import annotations

from sqlalchemy import String, Date, Numeric, DateTime, ForeignKey, Text, Enum as SQLEnum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.db import Base

from typing import Optional, TYPE_CHECKING
from datetime import datetime, date
from decimal import Decimal
from app.common.types import AccommodationType
import uuid

if TYPE_CHECKING:
    from app.models.trip import Trip


class Accommodation(Base):
    __tablename__ = "accommodations"

    __table_args__ = (
        CheckConstraint("check_out_date > check_in_date", name="check_accommodation_dates"),
    )

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

    name: Mapped[str] = mapped_column(String(200), nullable=False)

    type: Mapped[AccommodationType] = mapped_column(
        SQLEnum(AccommodationType, name="accommodation_type"),
        default=AccommodationType.hotel
    )

    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    check_in_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_out_date: Mapped[date] = mapped_column(Date, nullable=False)

    booking_reference: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True
    )

    cost: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        nullable=True
    )

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
        back_populates="accommodations"
    )