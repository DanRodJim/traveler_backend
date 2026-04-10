from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import uuid

from app.database.db import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService
from app.auth.dependencies import get_current_active_user
from app.models.user import User
from app.core.exceptions import (
    UserNotFoundError,
    DuplicateResourceError
)

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    service = UserService(db)
    
    if user_data.email and user_data.email != current_user.email:
        existing = service.get_by_email(user_data.email)
        if existing:
            raise DuplicateResourceError("Email", "email")
    
    updated_user: User | None = service.update(current_user.id, user_data)
    if not updated_user:
        raise UserNotFoundError()
    
    return UserResponse.model_validate(updated_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: uuid.UUID,
    db: Session = Depends(get_db)
) -> UserResponse:
    service = UserService(db)
    user: User | None = service.get_by_id(user_id)
    
    if not user:
        raise UserNotFoundError()
    
    return UserResponse.model_validate(user)