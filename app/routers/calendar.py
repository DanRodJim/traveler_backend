from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict

from app.database.db import get_db
from app.models.user import User
from app.services.calendar_service import CalendarService
from app.services.dashboard_service import DashboardService
from app.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/events", response_model=List[Dict])
async def get_calendar_events(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[Dict]:
    dashboard_service = DashboardService(db)
    trip_ids = dashboard_service.get_user_trip_ids(current_user.id)

    if not trip_ids:
        return []

    calendar_service = CalendarService(db)
    return calendar_service.get_events(trip_ids)