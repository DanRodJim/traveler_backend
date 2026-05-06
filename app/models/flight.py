from __future__ import annotations

from sqlalchemy import String, Date, Time, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.db import Base

from typing import Optional, TYPE_CHECKING
from datetime import datetime, date, time
from decimal import Decimal
import uuid

if TYPE_CHECKING:
    from app.models.trip import Trip


class Flight(Base):
    __tablename__ = "flights"

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

    airline: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    flight_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    departure_airport: Mapped[str] = mapped_column(String(3), nullable=False)  # IATA
    arrival_airport: Mapped[str] = mapped_column(String(3), nullable=False)    # IATA

    departure_date: Mapped[date] = mapped_column(Date, nullable=False)
    departure_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    arrival_date: Mapped[date] = mapped_column(Date, nullable=False)
    arrival_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    booking_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True, default="USD")

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
        back_populates="flights"
    )