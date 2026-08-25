from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
import uuid
from datetime import datetime

class ExpenseSplitBase(BaseModel):
    user_id: uuid.UUID
    amount: Decimal = Field(..., gt=0, decimal_places=2)

class ExpenseSplitCreate(ExpenseSplitBase):
    pass

class ExpenseSplitUpdate(BaseModel):
    is_paid: bool

class ExpenseSplitResponse(ExpenseSplitBase):
    id: uuid.UUID
    expense_id: uuid.UUID
    is_paid: bool = False
    paid_at: datetime | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
