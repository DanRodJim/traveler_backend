from sqlalchemy.orm import Session
from app.models.expense import Expense
from app.schemas.expense import ExpenseCreate, ExpenseUpdate
from typing import List, Optional
from decimal import Decimal
import uuid

class ExpenseService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_by_trip(self, trip_id: uuid.UUID) -> List[Expense]:
        return self.db.query(Expense).filter(
            Expense.trip_id == trip_id
        ).order_by(Expense.expense_date.desc()).all()
    
    def get_by_id(self, expense_id: uuid.UUID) -> Optional[Expense]:
        return self.db.query(Expense).filter(Expense.id == expense_id).first()
    
    def create(self, expense_data: ExpenseCreate, user_id: uuid.UUID) -> Expense:
        expense = Expense(
            id=uuid.uuid4(),
            paid_by=user_id,
            **expense_data.model_dump()
        )
        
        self.db.add(expense)
        self.db.commit()
        self.db.refresh(expense)
        return expense
    
    def update(self, expense_id: uuid.UUID, expense_data: ExpenseUpdate) -> Optional[Expense]:
        expense = self.get_by_id(expense_id)
        if not expense:
            return None
        
        update_data = expense_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(expense, field, value)
        
        self.db.commit()
        self.db.refresh(expense)
        return expense
    
    def delete(self, expense_id: uuid.UUID) -> bool:
        expense = self.get_by_id(expense_id)
        if not expense:
            return False
        
        self.db.delete(expense)
        self.db.commit()
        return True
    
    def get_total_by_trip(self, trip_id: uuid.UUID) -> Decimal:
        expenses = self.get_all_by_trip(trip_id)
        total = sum(expense.amount for expense in expenses)
        return Decimal(str(total))
    
    def get_by_user(self, trip_id: uuid.UUID, user_id: uuid.UUID) -> List[Expense]:
        return self.db.query(Expense).filter(
            Expense.trip_id == trip_id,
            Expense.paid_by == user_id
        ).all()