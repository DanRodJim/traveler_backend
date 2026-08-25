from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from app.common.types import ExpenseCategory
from app.schemas.expense_split import ExpenseSplitCreate, ExpenseSplitResponse
import uuid


class ExpenseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="USD", pattern=r'^[A-Z]{3}$')
    category: ExpenseCategory = ExpenseCategory.OTHER
    expense_date: date
    notes: Optional[str] = None
    paid_by: Optional[uuid.UUID] = None
    is_private: bool = True

    model_config = ConfigDict(from_attributes=True)


class ExpenseCreate(ExpenseBase):
    trip_id: uuid.UUID
    splits: Optional[List[ExpenseSplitCreate]] = None

    @model_validator(mode='after')
    def validate_paid_by_with_splits(self) -> 'ExpenseCreate':
        if self.splits and not self.paid_by:
            raise ValueError("paid_by is required when splits are provided")
        return self

class ExpenseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    currency: Optional[str] = Field(None, pattern=r'^[A-Z]{3}$')
    category: Optional[ExpenseCategory] = None
    expense_date: Optional[date] = None
    notes: Optional[str] = None
    paid_by: Optional[uuid.UUID] = None
    is_private: Optional[bool] = None
    splits: Optional[List[ExpenseSplitCreate]] = None

    @model_validator(mode='after')
    def validate_paid_by_with_splits(self) -> 'ExpenseUpdate':
        if self.splits and not self.paid_by:
            raise ValueError("paid_by is required when splits are provided")
        return self

    model_config = ConfigDict(from_attributes=True)


class ExpenseResponse(ExpenseBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    paid_by: Optional[uuid.UUID] = None
    splits: List[ExpenseSplitResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {'from_attributes': True}