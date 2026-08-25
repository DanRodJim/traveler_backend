from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
import uuid

from app.models.checklist_item import ChecklistItem
from app.schemas.checklist_item import (
    ChecklistItemCreate,
    ChecklistItemUpdate,
)
from app.core.exceptions import ChecklistNotFoundError, UnauthorizedError


class ChecklistService:
    def __init__(self, db: Session):
        self.db = db

    def get_by_trip(
        self,
        trip_id: uuid.UUID,
        current_user_id: uuid.UUID,
        list_type: Optional[str] = None
    ) -> List[ChecklistItem]:
        query = self.db.query(ChecklistItem).filter(
            ChecklistItem.trip_id == trip_id,
            or_(
                ChecklistItem.is_private == False,
                ChecklistItem.created_by == current_user_id
            )
        )

        if list_type:
            query = query.filter(ChecklistItem.list_type == list_type)

        return query.order_by(ChecklistItem.created_at.asc()).all()

    def get_by_id(self, item_id: uuid.UUID) -> Optional[ChecklistItem]:
        return self.db.query(ChecklistItem).filter(
            ChecklistItem.id == item_id
        ).first()

    def create(
        self,
        trip_id: uuid.UUID,
        current_user_id: uuid.UUID,
        item_data: ChecklistItemCreate
    ) -> ChecklistItem:
        item = ChecklistItem(
            id=uuid.uuid4(),
            trip_id=trip_id,
            created_by=current_user_id,
            list_type=item_data.list_type,
            title=item_data.title,
            is_private=item_data.is_private,
            is_completed=False,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update(
        self,
        item_id: uuid.UUID,
        current_user_id: uuid.UUID,
        item_data: ChecklistItemUpdate
    ) -> ChecklistItem:
        item = self.get_by_id(item_id)
        if not item:
            raise ChecklistNotFoundError()
        if item.created_by != current_user_id:
            raise UnauthorizedError("Only the creator can edit this item")

        update_dict = item_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(item, key, value)

        item.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(item)
        return item

    def toggle(
        self,
        item_id: uuid.UUID,
        current_user_id: uuid.UUID,
        is_completed: bool
    ) -> ChecklistItem:
        item = self.get_by_id(item_id)
        if not item:
            raise ChecklistNotFoundError()
        if item.created_by != current_user_id:
            raise UnauthorizedError("Only the creator can complete this item")

        item.is_completed = is_completed
        item.completed_at = datetime.now(timezone.utc) if is_completed else None
        item.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete(
        self,
        item_id: uuid.UUID,
        current_user_id: uuid.UUID
    ) -> bool:
        item = self.get_by_id(item_id)
        if not item:
            raise ChecklistNotFoundError()
        if item.created_by != current_user_id:
            raise UnauthorizedError("Only the creator can delete this item")

        self.db.delete(item)
        self.db.commit()
        return True