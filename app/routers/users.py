from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import uuid

from app.database.db import get_db
from app.schemas.user import NotificationPreferenceUpdate, UserResponse, UserUpdate, PasswordChange
from app.services.user_service import UserService
from app.auth.dependencies import get_current_active_user
from app.models.user import User
from app.core.security import verify_password
from app.core.exceptions import (
    UserNotFoundError,
    DuplicateResourceError,
    InvalidCredentialsError
)
from fastapi import status

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me")
async def get_my_profile(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.put("/me")
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


@router.get("/{user_id}")
async def get_user_by_id(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    service = UserService(db)
    user: User | None = service.get_by_id(user_id)
    
    if not user:
        raise UserNotFoundError()
    
    return UserResponse.model_validate(user)

@router.put("/me/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_my_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise InvalidCredentialsError()

    service = UserService(db)
    service.update(
        current_user.id,
        UserUpdate.model_validate({"password": password_data.new_password})
    )


@router.put("/me/notification-preferences")
async def update_notification_preferences(
    preference_data: NotificationPreferenceUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    service = UserService(db)
    updated_user = service.update(
        current_user.id,
        UserUpdate.model_validate({
            "email_notification_preference": preference_data.email_notification_preference
        })
    )
    if not updated_user:
        raise UserNotFoundError()
    return UserResponse.model_validate(updated_user)