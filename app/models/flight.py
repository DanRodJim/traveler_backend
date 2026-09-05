from __future__ import annotations

from sqlalchemy import Boolean, String, Date, Time, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.db import Base

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, date, time
from decimal import Decimal
import uuid

USERID = "users.id"

if TYPE_CHECKING:
    from app.models.trip import Trip
    from app.models.user import User


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

    departure_airport: Mapped[str] = mapped_column(String(3), nullable=False)
    arrival_airport: Mapped[str] = mapped_column(String(3), nullable=False)

    departure_date: Mapped[date] = mapped_column(Date, nullable=False)
    departure_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    arrival_date: Mapped[date] = mapped_column(Date, nullable=False)
    arrival_time: Mapped[Optional[time]] = mapped_column(Time, nullable=True)

    booking_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    cost: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True, default="USD")

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    paid_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(USERID),
        nullable=True
    )
    is_private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(USERID),
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

    payer: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[paid_by]
    )

    splits: Mapped[List["FlightSplit"]] = relationship(
        "FlightSplit",
        back_populates="flight",
        cascade="all, delete-orphan"
    )


# ── FlightSplit ───────────────────────────────────────────────────────────────

class FlightSplit(Base):
    __tablename__ = "flight_splits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    flight_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("flights.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey(USERID, ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now()
    )

    flight: Mapped[Flight] = relationship("Flight", back_populates="splits")
    user: Mapped["User"] = relationship("User")