from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import uuid

from app.database.db import get_db
from app.models.user import User
from app.services.pdf_service import PdfService
from app.auth.dependencies import get_current_active_user
from app.common.trip_utils import verify_trip_membership

router = APIRouter(prefix="/api/pdf", tags=["pdf"])


@router.get("/trip/{trip_id}/itinerary")
async def export_itinerary_pdf(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    verify_trip_membership(db, trip_id, current_user.id)

    service = PdfService(db)
    buffer = service.generate_itinerary_pdf(trip_id)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=itinerary-{trip_id}.pdf"}
    )


@router.get("/trip/{trip_id}/expenses")
async def export_expenses_pdf(
    trip_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    verify_trip_membership(db, trip_id, current_user.id)

    service = PdfService(db)
    buffer = await service.generate_expenses_pdf(trip_id, current_user.id)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=expenses-{trip_id}.pdf"}
    )