from typing import List, Optional
import uuid

from sqlalchemy.orm import Session

from app.models.notification import Notification
from app.core.exceptions import ResourceNotFoundError, UnauthorizedError


class NotificationNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Notification")


class NotificationService:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        user_id: uuid.UUID,
        notif_type: str,
        title: str,
        message: str,
        link: Optional[str] = None,
    ) -> Notification:
        notification = Notification(
            id=uuid.uuid4(),
            user_id=user_id,
            type=notif_type,
            title=title,
            message=message,
            link=link,
        )
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def get_by_user(
        self, user_id: uuid.UUID, unread_only: bool = False, limit: int = 50
    ) -> List[Notification]:
        query = self.db.query(Notification).filter(Notification.user_id == user_id)
        if unread_only:
            query = query.filter(Notification.is_read == False)
        return query.order_by(Notification.created_at.desc()).limit(limit).all()

    def get_unread_count(self, user_id: uuid.UUID) -> int:
        return (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .count()
        )

    def mark_as_read(self, notification_id: uuid.UUID, current_user_id: uuid.UUID) -> Notification:
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id
        ).first()

        if not notification:
            raise NotificationNotFoundError()
        if notification.user_id != current_user_id:
            raise UnauthorizedError("Not authorized to modify this notification")

        notification.is_read = True
        self.db.commit()
        self.db.refresh(notification)
        return notification

    def mark_all_as_read(self, user_id: uuid.UUID) -> int:
        updated = (
            self.db.query(Notification)
            .filter(Notification.user_id == user_id, Notification.is_read == False)
            .update({"is_read": True})
        )
        self.db.commit()
        return updated