import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import uuid

from sqlalchemy.orm import Session

from app.models.trip import Trip
from app.models.trip_invitation import TripInvitation
from app.models.trip_member import TripMember
from app.models.user import User
from app.core.exceptions import (
    ResourceNotFoundError,
    DuplicateResourceError,
    UnauthorizedError,
    TripNotFoundError,
)
from app.common.types import InvitationStatus, MemberRole
from app.schemas.trip_invitation import TripInvitationCreate, MyInvitationResponse
from app.services.notification_service import NotificationService
from app.services.email_service import EmailService
from app.core.config import settings

logger = logging.getLogger(__name__)

INVITATION_EXPIRY_DAYS = 7

_EMAIL_ENABLED_FOR_INVITATIONS = {"invitations_only", "all"}


class InvitationNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Invitation")


class InvitationExpiredError(UnauthorizedError):
    def __init__(self):
        super().__init__("This invitation has expired")


class InvitationAlreadyProcessedError(UnauthorizedError):
    def __init__(self):
        super().__init__("This invitation has already been processed")


class InvitationService:
    def __init__(self, db: Session):
        self.db = db
        self.notification_service = NotificationService(db)
        self.email_service = EmailService()

    def create_invitation(
        self,
        trip_id: uuid.UUID,
        invitation_data: TripInvitationCreate,
        invited_by: uuid.UUID,
    ) -> TripInvitation:
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise TripNotFoundError()

        if trip.owner_id != invited_by:
            raise UnauthorizedError("Only the trip owner can invite members")

        existing_user = self.db.query(User).filter(User.email == invitation_data.email).first()
        if existing_user:
            existing_member = self.db.query(TripMember).filter(
                TripMember.trip_id == trip_id,
                TripMember.user_id == existing_user.id,
            ).first()
            if existing_member:
                raise DuplicateResourceError("Member", "email")

        existing_invitation = self.db.query(TripInvitation).filter(
            TripInvitation.trip_id == trip_id,
            TripInvitation.invited_email == invitation_data.email,
            TripInvitation.status == "pending",
        ).first()
        if existing_invitation:
            raise DuplicateResourceError("Invitation", "email")

        invitation = TripInvitation(
            id=uuid.uuid4(),
            trip_id=trip_id,
            invited_email=invitation_data.email,
            invited_by=invited_by,
            role=invitation_data.role.value,
            status="pending",
            token=secrets.token_urlsafe(32),
            expires_at=datetime.now(timezone.utc) + timedelta(days=INVITATION_EXPIRY_DAYS),
        )
        self.db.add(invitation)
        self.db.commit()
        self.db.refresh(invitation)

        self._notify_invitee(invitation, trip, invited_by)

        return invitation

    def _notify_invitee(self, invitation: TripInvitation, trip: Trip, invited_by: uuid.UUID) -> None:
        inviter = self.db.query(User).filter(User.id == invited_by).first()
        inviter_name = inviter.full_name if inviter else "Someone"

        invite_url = f"{settings.FRONTEND_URL}/dashboard/invitations"

        existing_user = self.db.query(User).filter(
            User.email == invitation.invited_email
        ).first()

        if existing_user:
            self.notification_service.create(
                user_id=existing_user.id,
                notif_type="invitation",
                title="Trip invitation",
                message=f"{inviter_name} invited you to join \"{trip.title}\"",
                link="/dashboard/invitations",
            )

        should_send_email = (
            existing_user is None
            or existing_user.email_notification_preference in _EMAIL_ENABLED_FOR_INVITATIONS
        )

        if should_send_email:
            self.email_service.send_invitation_email(
                to_email=invitation.invited_email,
                inviter_name=inviter_name,
                trip_title=trip.title,
                role=invitation.role,
                invite_url=invite_url,
            )

    def get_pending_by_trip(self, trip_id: uuid.UUID, current_user_id: uuid.UUID) -> List[TripInvitation]:
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise TripNotFoundError()
        if trip.owner_id != current_user_id:
            raise UnauthorizedError("Only the trip owner can view invitations")

        return self.db.query(TripInvitation).filter(
            TripInvitation.trip_id == trip_id,
            TripInvitation.status == "pending",
        ).all()

    def revoke_invitation(
        self, trip_id: uuid.UUID, invitation_id: uuid.UUID, current_user_id: uuid.UUID
    ) -> None:
        trip = self.db.query(Trip).filter(Trip.id == trip_id).first()
        if not trip:
            raise TripNotFoundError()
        if trip.owner_id != current_user_id:
            raise UnauthorizedError("Only the trip owner can revoke invitations")

        invitation = self.db.query(TripInvitation).filter(
            TripInvitation.id == invitation_id, TripInvitation.trip_id == trip_id
        ).first()
        if not invitation:
            raise InvitationNotFoundError()

        self.db.delete(invitation)
        self.db.commit()

    def get_my_pending_invitations(self, user_email: str) -> List[MyInvitationResponse]:
        self._expire_stale_invitations(user_email)
        invitations = self.db.query(TripInvitation).filter(
            TripInvitation.invited_email == user_email,
            TripInvitation.status == "pending",
        ).all()
        return [self._to_my_invitation_response(inv) for inv in invitations]

    def get_by_token(self, token: str) -> Optional[TripInvitation]:
        return self.db.query(TripInvitation).filter(TripInvitation.token == token).first()

    def get_invitation_details_by_token(self, token: str) -> Optional[MyInvitationResponse]:
        invitation = self.get_by_token(token)
        if not invitation:
            return None
        return self._to_my_invitation_response(invitation)

    def _expire_stale_invitations(self, user_email: str) -> None:
        now = datetime.now(timezone.utc)
        stale = self.db.query(TripInvitation).filter(
            TripInvitation.invited_email == user_email,
            TripInvitation.status == "pending",
            TripInvitation.expires_at < now,
        ).all()
        for inv in stale:
            inv.status = InvitationStatus.EXPIRED
        if stale:
            self.db.commit()

    def accept_invitation(self, token: str, current_user: User) -> TripMember:
        invitation = self.get_by_token(token)
        if not invitation:
            raise InvitationNotFoundError()

        if invitation.invited_email.lower() != current_user.email.lower():
            raise UnauthorizedError("This invitation was not sent to your email")

        if invitation.status != "pending":
            raise InvitationAlreadyProcessedError()

        if invitation.expires_at < datetime.now(timezone.utc):
            invitation.status = InvitationStatus.EXPIRED
            self.db.commit()
            raise InvitationExpiredError()

        existing_member = self.db.query(TripMember).filter(
            TripMember.trip_id == invitation.trip_id,
            TripMember.user_id == current_user.id,
        ).first()
        if existing_member:
            invitation.status = InvitationStatus.ACCEPTED
            self.db.commit()
            raise DuplicateResourceError("Member", "email")

        member = TripMember(
            id=uuid.uuid4(),
            trip_id=invitation.trip_id,
            user_id=current_user.id,
            role=invitation.role,
        )
        self.db.add(member)
        invitation.status = InvitationStatus.ACCEPTED
        invitation.updated_at = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(member)
        return member

    def decline_invitation(self, token: str, current_user: User) -> TripInvitation:
        invitation = self.get_by_token(token)
        if not invitation:
            raise InvitationNotFoundError()

        if invitation.invited_email.lower() != current_user.email.lower():
            raise UnauthorizedError("This invitation was not sent to your email")

        if invitation.status != "pending":
            raise InvitationAlreadyProcessedError()

        invitation.status = InvitationStatus.DECLINED
        invitation.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(invitation)
        return invitation

    def _to_my_invitation_response(self, invitation: TripInvitation) -> MyInvitationResponse:
        trip = self.db.query(Trip).filter(Trip.id == invitation.trip_id).first()

        return MyInvitationResponse(
            id=invitation.id,
            trip_id=invitation.trip_id,
            trip_title=trip.title if trip else "Unknown trip",
            trip_destination=trip.destination if trip else "",
            inviter_name=invitation.inviter.full_name,
            role=invitation.role,
            status=invitation.status,
            token=invitation.token,
            expires_at=invitation.expires_at,
            created_at=invitation.created_at,
        )