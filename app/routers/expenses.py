from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
import uuid

from app.database.db import get_db
from app.schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from app.services.expense_service import ExpenseService
from app.services.trip_service import TripService
from app.auth.dependencies import get_current_active_user
from app.models.user import User
from app.models.expense import Expense
from app.core.exceptions import (
    ExpenseNotFoundError,
    UnauthorizedError,
    InsufficientPermissionsError
)

router = APIRouter(prefix="/api/expenses", tags=["expenses"])


@router.get("/", response_model=List[ExpenseResponse])
async def get_expenses(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[ExpenseResponse]:
    trip_service = TripService(db)
    if not trip_service.has_view_permission(trip_id, current_user.id):
        raise UnauthorizedError("Not authorized to view this trip")
    
    service = ExpenseService(db)
    expenses: List[Expense] = service.get_all_by_trip(trip_id)
    
    return [ExpenseResponse.model_validate(expense) for expense in expenses]


@router.get("/total/{trip_id}")
async def get_total_expenses(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict:
    trip_service = TripService(db)
    if not trip_service.has_view_permission(trip_id, current_user.id):
        raise UnauthorizedError("Not authorized to view this trip")
    
    service = ExpenseService(db)
    total: Decimal = service.get_total_by_trip(trip_id)
    
    return {"trip_id": str(trip_id), "total": float(total)}


@router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ExpenseResponse:
    service = ExpenseService(db)
    expense: Expense | None = service.get_by_id(expense_id)
    
    if not expense:
        raise ExpenseNotFoundError()
    
    trip_service = TripService(db)
    if not trip_service.has_view_permission(expense.trip_id, current_user.id):
        raise UnauthorizedError("Not authorized to view this expense")
    
    return ExpenseResponse.model_validate(expense)


@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense_data: ExpenseCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ExpenseResponse:
    trip_service = TripService(db)
    if not trip_service.has_edit_permission(expense_data.trip_id, current_user.id):
        raise InsufficientPermissionsError("editor")
    
    service = ExpenseService(db)
    expense: Expense = service.create(expense_data, current_user.id)
    
    return ExpenseResponse.model_validate(expense)


@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: uuid.UUID,
    expense_data: ExpenseUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> ExpenseResponse:
    service = ExpenseService(db)
    expense: Expense | None = service.get_by_id(expense_id)
    
    if not expense:
        raise ExpenseNotFoundError()
    
    trip_service = TripService(db)
    if not trip_service.has_edit_permission(expense.trip_id, current_user.id):
        raise InsufficientPermissionsError("editor")
    
    updated: Expense | None = service.update(expense_id, expense_data)
    if not updated:
        raise ExpenseNotFoundError()
    
    return ExpenseResponse.model_validate(updated)


@router.delete("/{expense_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense(
    expense_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    service = ExpenseService(db)
    expense: Expense | None = service.get_by_id(expense_id)
    
    if not expense:
        raise ExpenseNotFoundError()
    
    trip_service = TripService(db)
    if not trip_service.has_edit_permission(expense.trip_id, current_user.id):
        raise InsufficientPermissionsError("editor")
    
    service.delete(expense_id)