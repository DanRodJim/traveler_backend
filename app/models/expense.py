from __future__ import annotations

from sqlalchemy import String, Date, Numeric, DateTime, ForeignKey, Text, Enum as SQLEnum, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.db import Base

from typing import Optional, List, TYPE_CHECKING
from datetime import datetime, date
from decimal import Decimal
from app.common.types import ExpenseCategory
import uuid

if TYPE_CHECKING:
    from app.models.trip import Trip


class Expense(Base):
    __tablename__ = "expenses"

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

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    currency: Mapped[str] = mapped_column(String(3), default="USD")

    category: Mapped[ExpenseCategory] = mapped_column(
        SQLEnum(ExpenseCategory, name="expense_category"),
        default=ExpenseCategory.other
    )

    expense_date: Mapped[date] = mapped_column(Date, nullable=False)

    paid_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )

    split_between: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

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
        back_populates="expenses"
    )