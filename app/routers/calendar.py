from fastapi import APIRouter
from typing import List, Dict
from app.services.calendar_service import CalendarService
from app.services.dashboard_service import DashboardService
from app.auth.dependencies import CurrentUser, DbSession

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


@router.get("/events")
async def get_calendar_events(
    current_user: CurrentUser, db: DbSession
) -> List[Dict]:
    dashboard_service = DashboardService(db)
    trip_ids = dashboard_service.get_user_trip_ids(current_user.id)

    if not trip_ids:
        return []

    calendar_service = CalendarService(db)
    return calendar_service.get_events(trip_ids)