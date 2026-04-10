from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal
from app.common.types import ExpenseCategory
import uuid

class ExpenseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="USD", pattern=r'^[A-Z]{3}$')
    category: ExpenseCategory = ExpenseCategory.other
    expense_date: date
    split_between: Optional[List[str]] = None
    notes: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    trip_id: uuid.UUID

class ExpenseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    currency: Optional[str] = Field(None, pattern=r'^[A-Z]{3}$')
    category: Optional[ExpenseCategory] = None
    expense_date: Optional[date] = None
    split_between: Optional[List[str]] = None
    notes: Optional[str] = None

class ExpenseResponse(ExpenseBase):
    id: uuid.UUID
    trip_id: uuid.UUID
    paid_by: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True