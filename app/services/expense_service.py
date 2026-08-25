from datetime import datetime, timezone

from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from decimal import Decimal
import uuid

from app.core.exceptions import ExpenseNotFoundError, UnauthorizedError
from app.models.expense import Expense, ExpenseSplit
from app.schemas.expense import ExpenseCreate, ExpenseUpdate


class ExpenseService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, expense_id: uuid.UUID) -> Optional[Expense]:
        return self.db.query(Expense).filter(Expense.id == expense_id).first()
    
    def get_all_by_trip(self, trip_id: uuid.UUID, current_user_id: uuid.UUID) -> List[Expense]:
        public_expenses = (
            self.db.query(Expense)
            .filter(
                Expense.trip_id == trip_id,
                Expense.is_private == False
            )
            .all()
        )

        private_expenses = (
            self.db.query(Expense)
            .outerjoin(ExpenseSplit, ExpenseSplit.expense_id == Expense.id)
            .filter(
                Expense.trip_id == trip_id,
                Expense.is_private == True,
                or_(
                    Expense.paid_by == current_user_id,
                    ExpenseSplit.user_id == current_user_id
                )
            )
            .distinct()
            .all()
        )

        all_expenses = list({e.id: e for e in public_expenses + private_expenses}.values())
        all_expenses.sort(key=lambda e: e.expense_date, reverse=True)

        return all_expenses
    
    def get_total_by_trip(self, trip_id: uuid.UUID) -> Decimal:
        result = self.db.query(Expense).filter(
            Expense.trip_id == trip_id
        ).with_entities(
            Expense.amount
        ).all()
        
        return sum((expense.amount for expense in result), Decimal("0"))
    
    def create_with_splits(self, expense_data: ExpenseCreate) -> Expense:
        expense_dict = expense_data.model_dump(exclude={'splits'})
        expense = Expense(**expense_dict)
        
        self.db.add(expense)
        self.db.flush()

        if expense_data.splits:
            for split_data in expense_data.splits:
                is_payer = split_data.user_id == expense_data.paid_by
                
                split = ExpenseSplit(
                    expense_id=expense.id,
                    user_id=split_data.user_id,
                    amount=split_data.amount,
                    is_paid=is_payer,
                    paid_at=datetime.now(timezone.utc) if is_payer else None,
                )
                self.db.add(split)

        self.db.commit()
        self.db.refresh(expense)
        return expense
    
    def create(self, expense_data: ExpenseCreate, created_by: uuid.UUID) -> Expense:
        if not expense_data.paid_by:
            expense_data.paid_by = created_by
        
        return self.create_with_splits(expense_data)
    
    def update_with_splits(
        self,
        expense_id: uuid.UUID,
        expense_data: ExpenseUpdate
    ) -> Expense | None:
        expense = self.get_by_id(expense_id)
        
        if not expense:
            return None

        update_dict = expense_data.model_dump(exclude={'splits'}, exclude_unset=True)
        for key, value in update_dict.items():
            setattr(expense, key, value)

        if expense_data.splits is not None:
            self.db.query(ExpenseSplit).filter(
                ExpenseSplit.expense_id == expense_id
            ).delete()

            paid_by = expense_data.paid_by or expense.paid_by

            for split_data in expense_data.splits:
                is_payer = split_data.user_id == paid_by

                split = ExpenseSplit(
                    expense_id=expense.id,
                    user_id=split_data.user_id,
                    amount=split_data.amount,
                    is_paid=is_payer,
                    paid_at=datetime.now(timezone.utc) if is_payer else None,
                )
                self.db.add(split)

        self.db.commit()
        self.db.refresh(expense)
        return expense
    
    def update(
        self, 
        expense_id: uuid.UUID, 
        expense_data: ExpenseUpdate
    ) -> Optional[Expense]:
        return self.update_with_splits(expense_id, expense_data)
    
    def delete(self, expense_id: uuid.UUID) -> bool:
        expense = self.get_by_id(expense_id)
        
        if not expense:
            return False
        
        self.db.delete(expense)
        self.db.commit()
        
        return True
    
    def mark_split_as_paid(
        self,
        expense_id: uuid.UUID,
        split_id: uuid.UUID,
        current_user_id: uuid.UUID
    ) -> ExpenseSplit:
        expense = self.get_by_id(expense_id)
        if not expense:
            raise ExpenseNotFoundError()

        if expense.paid_by != current_user_id:
            raise UnauthorizedError("Only the payer can mark splits as paid")

        split = (
            self.db.query(ExpenseSplit)
            .filter(
                ExpenseSplit.id == split_id,
                ExpenseSplit.expense_id == expense_id
            )
            .first()
        )

        if not split:
            raise ExpenseNotFoundError()

        split.is_paid = True
        split.paid_at = datetime.now(timezone.utc)
        split.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(split)

        return split

    def unmark_split_as_paid(
        self,
        expense_id: uuid.UUID,
        split_id: uuid.UUID,
        current_user_id: uuid.UUID
    ) -> ExpenseSplit:
        expense = self.get_by_id(expense_id)
        if not expense:
            raise ExpenseNotFoundError()

        if expense.paid_by != current_user_id:
            raise UnauthorizedError("Only the payer can unmark splits as paid")

        split = (
            self.db.query(ExpenseSplit)
            .filter(
                ExpenseSplit.id == split_id,
                ExpenseSplit.expense_id == expense_id
            )
            .first()
        )

        if not split:
            raise ExpenseNotFoundError()

        split.is_paid = False
        split.paid_at = None
        split.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(split)

        return split