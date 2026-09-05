from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.database.db import get_db
from app.models.user import User
from app.schemas.trip_invitation import MyInvitationResponse
from app.schemas.trip_member import TripMemberResponse
from app.services.invitation_service import InvitationService, InvitationNotFoundError
from app.auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/invitations", tags=["invitations"])


@router.get("/me")
async def get_my_invitations(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[MyInvitationResponse]:
    service = InvitationService(db)
    return service.get_my_pending_invitations(current_user.email)


@router.get("/{token}")
async def get_invitation_by_token(
    token: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> MyInvitationResponse:
    service = InvitationService(db)
    result = service.get_invitation_details_by_token(token)
    if not result:
        raise InvitationNotFoundError()
    return result


@router.post("/{token}/accept")
async def accept_invitation(
    token: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> TripMemberResponse:
    service = InvitationService(db)
    member = service.accept_invitation(token, current_user)
    return TripMemberResponse.model_validate(member)


@router.post("/{token}/decline")
async def decline_invitation(
    token: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> dict:
    service = InvitationService(db)
    service.decline_invitation(token, current_user)
    return {"detail": "Invitation declined"}