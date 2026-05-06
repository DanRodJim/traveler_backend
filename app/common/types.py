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