from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database.db import get_db
from app.models.user import User
from app.services.dashboard_service import DashboardService
from app.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    service = DashboardService(db)
    
    trip_ids = service.get_user_trip_ids(current_user.id)
    
    if not trip_ids:
        return {
            "total_trips": 0,
            "trips_by_status": {
                "planning": 0,
                "confirmed": 0,
                "in_progress": 0,
                "completed": 0,
                "cancelled": 0
            },
            "total_expenses": {},
            "expenses_by_category": {},
            "expenses_by_trip": [],
            "upcoming_activities": [],
            "next_trip": None,
            "expenses_by_type": {},
            "activities_by_category": {},
            "accommodations_by_type": {},
        }
    
    return {
        "total_trips": len(trip_ids),
        "trips_by_status": service.get_trips_by_status(trip_ids),
        "total_expenses": service.get_total_expenses_by_currency(trip_ids),
        "expenses_by_category": service.get_expenses_by_category(trip_ids),
        "expenses_by_trip": service.get_top_trips_by_spending(trip_ids),
        "upcoming_activities": service.get_upcoming_activities(trip_ids),
        "next_trip": service.get_next_trip(trip_ids),
        "expenses_by_type": service.get_expenses_by_type(trip_ids),
        "activities_by_category": service.get_activities_by_category(trip_ids),
        "accommodations_by_type": service.get_accommodations_by_type(trip_ids),
    }