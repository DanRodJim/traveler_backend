from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Dict
import uuid

from app.database.db import get_db
from app.models.user import User
from app.models.trip_member import TripMember
from app.services.balance_service import BalanceService
from app.auth.dependencies import get_current_active_user
from app.schemas.balance import SettleRequest
from app.common.trip_utils import verify_trip_membership

router = APIRouter(prefix="/api/balances", tags=["balances"])


@router.get("/trip/{trip_id}")
async def get_trip_balances(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict:
    verify_trip_membership(db, trip_id, current_user.id)

    service = BalanceService(db)
    return service.calculate_trip_balances(trip_id, current_user.id)


@router.get("/trip/{trip_id}/user/{user_id}")
async def get_user_balance_in_trip(
    trip_id: uuid.UUID,
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict:
    verify_trip_membership(db, trip_id, current_user.id)

    service = BalanceService(db)
    return service.calculate_user_balance_in_trip(trip_id, user_id)


@router.get("/trip/{trip_id}/me")
async def get_my_balance_in_trip(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict:
    verify_trip_membership(db, trip_id, current_user.id)

    service = BalanceService(db)
    return service.calculate_user_balance_in_trip(trip_id, current_user.id)


@router.post("/trip/{trip_id}/settle")
async def settle_balance(
    trip_id: uuid.UUID,
    settle_data: SettleRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict:
    verify_trip_membership(db, trip_id, current_user.id)

    if current_user.id != settle_data.to_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creditor can mark this settlement as paid"
        )

    service = BalanceService(db)
    settled_count = service.settle_between_users(
        trip_id=trip_id,
        from_user_id=settle_data.from_user_id,
        to_user_id=settle_data.to_user_id,
        currency=settle_data.currency
    )

    if settled_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pending splits found between these users"
        )

    updated_balances = service.calculate_trip_balances(trip_id, current_user.id)

    return {
        'settled_splits': settled_count,
        'balances': updated_balances
    }