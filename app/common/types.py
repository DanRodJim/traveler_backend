from enum import Enum

class AccommodationType(str, Enum):
    HOTEL = "hotel"
    AIRBNB = "airbnb"
    HOSTEL = "hostel"
    RESORT = "resort"
    APARTMENT = "apartment"
    OTHER = "other"

class ActivityCategory(str, Enum):
    SIGHTSEEING = "sightseeing"
    RESTAURANT = "restaurant"
    TRANSPORT = "transport"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"
    OTHER = "other"

class ExpenseCategory(str, Enum):
    FOOD = "food"
    TRANSPORT = "transport"
    ACTIVITY = "activity"
    ACCOMMODATION = "accommodation"
    SHOPPING = "shopping"
    OTHER = "other"

class TripStatus(str, Enum):
    PLANNING = "planning"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MemberRole(str, Enum):
    OWNER = "owner"
    EDITOR = "editor"
    VIEWER = "viewer"


class NotificationPreference(str, Enum):
    NONE = "none"
    INVITATIONS_ONLY = "invitations_only"
    ALERTS_ONLY = "alerts_only"
    ALL = "all"


class NotificationType(str, Enum):
    INVITATION = "invitation"
    TRIP_REMINDER = "trip_reminder"


class InvitationStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"