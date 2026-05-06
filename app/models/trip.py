from __future__ import annotations

from sqlalchemy import String, Date, Numeric, DateTime, ForeignKey, Text, Enum as SQLEnum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.db import Base

from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from app.common.types import TripStatus
from datetime import datetime, date
import uuid

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.activity import Activity
    from app.models.flight import Flight
    from app.models.accommodation import Accommodation
    from app.models.expense import Expense
    from app.models.trip_member import TripMember


class Trip(Base):
    __tablename__ = "trips"
    
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="check_trip_dates"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    destination: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    budget: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True, default="USD")

    status: Mapped[TripStatus] = mapped_column(
        SQLEnum(
            *[status.value for status in TripStatus],
            name='trip_status'
        ),
        nullable=False, 
        default=TripStatus.PLANNING.value
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
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
    owner: Mapped[User] = relationship(
        "User",
        back_populates="owned_trips",
        foreign_keys=[owner_id],
        lazy="select"
    )
    members: Mapped[List[TripMember]] = relationship(
        "TripMember",
        back_populates="trip",
        cascade="all, delete-orphan",
        lazy="select"
    )
    activities: Mapped[List[Activity]] = relationship(
        "Activity",
        back_populates="trip",
        cascade="all, delete-orphan",
        lazy="select"
    )
    flights: Mapped[List[Flight]] = relationship(
        "Flight",
        back_populates="trip",
        cascade="all, delete-orphan",
        lazy="select"
    )
    accommodations: Mapped[List[Accommodation]] = relationship(
        "Accommodation",
        back_populates="trip",
        cascade="all, delete-orphan",
        lazy="select"
    )
    expenses: Mapped[List[Expense]] = relationship(
        "Expense",
        back_populates="trip",
        cascade="all, delete-orphan",
        lazy="select"
    )
