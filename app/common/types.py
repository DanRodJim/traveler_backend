from enum import Enum

class AccommodationType(str, Enum):
    hotel = "hotel"
    airbnb = "airbnb"
    hostel = "hostel"
    resort = "resort"
    apartment = "apartment"
    other = "other"

class ActivityCategory(str, Enum):
    sightseeing = "sightseeing"
    restaurant = "restaurant"
    transport = "transport"
    entertainment = "entertainment"
    shopping = "shopping"
    other = "other"

class ExpenseCategory(str, Enum):
    food = "food"
    transport = "transport"
    activity = "activity"
    accommodation = "accommodation"
    shopping = "shopping"
    other = "other"

class TripStatus(str, Enum):
    planning = "planning"
    confirmed = "confirmed"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"

class MemberRole(str, Enum):
    owner = "owner"
    editor = "editor"
    viewer = "viewer"