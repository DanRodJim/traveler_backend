from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.db import get_db
from app.services.trip_reminder_service import TripReminderService
from app.core.config import settings
from app.auth.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/api/dev", tags=["dev-tools"])


@router.post("/trigger-trip-reminders")
async def trigger_trip_reminders(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict:
    if not settings.is_development():
        return {"error": "This endpoint is only available in development"}

    service = TripReminderService(db)
    sent_count = service.send_due_reminders()
    return {"reminders_sent": sent_count}