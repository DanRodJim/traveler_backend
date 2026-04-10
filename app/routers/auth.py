from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.database.db import get_db
from app.schemas.auth import Token
from app.schemas.user import UserResponse, UserCreate
from app.services.user_service import UserService
from app.core.security import create_access_token
from app.core.config import settings
from app.auth.dependencies import get_current_active_user
from app.models.user import User
from app.core.exceptions import (
    DuplicateResourceError,
    InvalidCredentialsError,
    UserInactiveError
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
) -> UserResponse:
    service = UserService(db)
    
    existing_user = service.get_by_email(user_data.email)
    if existing_user:
        raise DuplicateResourceError("User", "email")
    
    user: User = service.create(user_data)
    return UserResponse.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Token:
    service = UserService(db)
    
    user: User | None = service.authenticate(form_data.username, form_data.password)
    if not user:
        raise InvalidCredentialsError()
    
    if not user.is_active:
        raise UserInactiveError()
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    return UserResponse.model_validate(current_user)