from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List, Dict
import uuid

from app.database.db import get_db
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.services.notification_service import NotificationService
from app.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.get("/")
async def get_my_notifications(
    unread_only: bool = False,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[NotificationResponse]:
    service = NotificationService(db)
    notifications = service.get_by_user(current_user.id, unread_only)
    return [NotificationResponse.model_validate(n) for n in notifications]


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, int]:
    service = NotificationService(db)
    return {"count": service.get_unread_count(current_user.id)}


@router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> NotificationResponse:
    service = NotificationService(db)
    notification = service.mark_as_read(notification_id, current_user.id)
    return NotificationResponse.model_validate(notification)


@router.patch("/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> None:
    service = NotificationService(db)
    service.mark_all_as_read(current_user.id)