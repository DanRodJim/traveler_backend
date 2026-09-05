from __future__ import annotations

from sqlalchemy import Boolean, String, Date, Numeric, DateTime, ForeignKey, Text, Enum as SQLEnum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.db import Base

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, date
from decimal import Decimal
from app.common.types import AccommodationType
import uuid

USERID = "users.id"

if TYPE_CHECKING:
    from app.models.trip import Trip
    from app.models.user import User


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
        SQLEnum(
            *[t.value for t in AccommodationType],
            name='accommodation_type'
        ),
        nullable=False
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

    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True, default="USD")

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    latitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[Optional[Decimal]] = mapped_column(Numeric(9, 6), nullable=True)

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
        back_populates="accommodations"
    )

    payer: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[paid_by]
    )

    splits: Mapped[List["AccommodationSplit"]] = relationship(
        "AccommodationSplit",
        back_populates="accommodation",
        cascade="all, delete-orphan"
    )


# ── AccommodationSplit ────────────────────────────────────────────────────────

class AccommodationSplit(Base):
    __tablename__ = "accommodation_splits"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    accommodation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accommodations.id", ondelete="CASCADE"), nullable=False, index=True
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

    accommodation: Mapped[Accommodation] = relationship("Accommodation", back_populates="splits")
    user: Mapped["User"] = relationship("User")