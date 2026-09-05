from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict
import uuid

from app.database.db import get_db
from app.models.user import User
from app.services.budget_service import BudgetService
from app.auth.dependencies import get_current_active_user
from app.common.trip_utils import verify_trip_membership
from app.services.personal_budget_service import PersonalBudgetService

router = APIRouter(prefix="/api/budget", tags=["budget"])

@router.get("/trip/{trip_id}")
async def get_trip_budget_summary(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict:
    verify_trip_membership(db, trip_id, current_user.id)

    service = BudgetService(db)
    return await service.get_trip_budget_summary(trip_id)


@router.get("/trip/{trip_id}/me")
async def get_my_personal_budget_summary(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict:
    verify_trip_membership(db, trip_id, current_user.id)

    service = PersonalBudgetService(db)
    return await service.get_personal_budget_summary(trip_id, current_user.id)