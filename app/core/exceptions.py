class AppException(Exception):
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


# --- Database errors ---

class DatabaseConstraintError(AppException):
    def __init__(self, message: str = "Database constraint violation"):
        super().__init__(message, status_code=400)


class InvalidDateRangeError(DatabaseConstraintError):
    def __init__(self, field: str = "date range"):
        super().__init__(f"Invalid {field}: end date must be after start date")


class DuplicateResourceError(DatabaseConstraintError):
    def __init__(self, resource: str = "Resource", field: str = ""):
        field_msg = f" ({field})" if field else ""
        super().__init__(f"{resource} already exists{field_msg}")


class ForeignKeyError(DatabaseConstraintError):
    def __init__(self, resource: str = "Referenced resource"):
        super().__init__(f"{resource} not found")


class NotNullError(DatabaseConstraintError):
    def __init__(self, field: str = "Field"):
        super().__init__(f"{field} is required")


# --- Resources errors ---

class ResourceNotFoundError(AppException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", status_code=404)


class TripNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Trip")


class ActivityNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Activity")


class FlightNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Flight")


class AccommodationNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Accommodation")


class ExpenseNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Expense")


class UserNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("User")


# --- Authorization errors ---

class UnauthorizedError(AppException):
    def __init__(self, message: str = "Not authorized to perform this action"):
        super().__init__(message, status_code=403)


class NotTripOwnerError(UnauthorizedError):
    def __init__(self):
        super().__init__("Only trip owner can perform this action")


class InsufficientPermissionsError(UnauthorizedError):
    def __init__(self, required_role: str = "editor"):
        super().__init__(f"Requires {required_role} permissions or higher")


# --- Authentication errors ---

class AuthenticationError(AppException):
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status_code=401)


class InvalidCredentialsError(AuthenticationError):
    def __init__(self):
        super().__init__("Incorrect email or password")


class InvalidTokenError(AuthenticationError):
    def __init__(self):
        super().__init__("Invalid or expired token")


class UserInactiveError(AuthenticationError):
    def __init__(self):
        super().__init__("User account is inactive")


# --- Validation errors ---

class ValidationError(AppException):
    def __init__(self, message: str):
        super().__init__(message, status_code=422)


class InvalidInputError(ValidationError):
    def __init__(self, field: str, reason: str):
        super().__init__(f"Invalid {field}: {reason}")