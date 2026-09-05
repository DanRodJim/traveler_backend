from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.db import Base

from typing import TYPE_CHECKING
from datetime import datetime
import uuid

if TYPE_CHECKING:
    from app.models.trip import Trip
    from app.models.user import User


class TripReminderLog(Base):
    __tablename__ = "trip_reminder_logs"

    __table_args__ = (
        UniqueConstraint("trip_id", "user_id", "days_before", name="uq_trip_reminder_once"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    trip_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("trips.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    days_before: Mapped[int] = mapped_column(Integer, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=text("now()"), nullable=False
    )

    trip: Mapped["Trip"] = relationship("Trip")
    user: Mapped["User"] = relationship("User")