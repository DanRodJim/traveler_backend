import traceback

from fastapi import Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import ValidationError as PydanticValidationError
import logging
import re

from app.core.config import settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


def _sanitize_for_log(value: str, max_length: int = 500) -> str:
    """
    Elimina saltos de línea y caracteres de control de un string antes de
    escribirlo en el log, para prevenir log injection (CRLF injection).
    También limita la longitud para evitar logs excesivamente largos.
    """
    sanitized = re.sub(r'[\r\n\t]+', ' ', value)
    sanitized = re.sub(r'[\x00-\x1f\x7f]', '', sanitized)
    return sanitized[:max_length]


def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppException):
        logger.error(f"Unexpected exception type in app_exception_handler: {type(exc)}")
        raise exc

    logger.error(
        "%s: %s | Path: %s | Method: %s",
        exc.__class__.__name__,
        _sanitize_for_log(exc.message),
        _sanitize_for_log(str(request.url.path)),
        request.method,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "path": str(request.url.path)
        }
    )


_CONSTRAINT_RULES: list[tuple[str, str, str]] = [
    ("check_trip_dates", "End date must be after start date", "InvalidDateRangeError"),
    ("check_accommodation_dates", "Check-out date must be after check-in date", "InvalidDateRangeError"),
    ("check_activity_times", "End time must be after start time", "InvalidDateRangeError"),
]


def _classify_integrity_error(error_message: str) -> tuple[str, str]:
    """
    Determina el mensaje amigable y el tipo de error a partir del mensaje
    crudo de IntegrityError. Extraído a su propia función para mantener
    baja la complejidad cognitiva de integrity_error_handler.
    """
    for pattern, message, error_type in _CONSTRAINT_RULES:
        if pattern in error_message:
            return message, error_type

    if "unique" in error_message or "duplicate" in error_message:
        message = "Email already registered" if "email" in error_message else "Resource already exists"
        return message, "DuplicateResourceError"

    if "foreign key" in error_message:
        return "Referenced resource not found", "ForeignKeyError"

    if "not null" in error_message or "null value" in error_message:
        match = re.search(r'column "(\w+)"', error_message)
        field = match.group(1) if match else "Field"
        return f"{field} is required", "NotNullError"

    return "Database constraint violation", "DatabaseConstraintError"


def integrity_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, IntegrityError):
        logger.error(f"Unexpected exception type in integrity_error_handler: {type(exc)}")
        raise exc

    error_message = str(exc.orig).lower()

    logger.error(
        "IntegrityError: %s | Path: %s | Method: %s",
        _sanitize_for_log(error_message),
        _sanitize_for_log(str(request.url.path)),
        request.method,
    )

    message, error_type = _classify_integrity_error(error_message)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": error_type,
            "message": message,
            "path": str(request.url.path)
        }
    )


def sqlalchemy_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, SQLAlchemyError):
        logger.error(f"Unexpected exception type in sqlalchemy_error_handler: {type(exc)}")
        raise exc

    logger.error(
        "SQLAlchemyError: %s | Path: %s | Method: %s",
        _sanitize_for_log(str(exc)),
        _sanitize_for_log(str(request.url.path)),
        request.method,
        exc_info=True
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "DatabaseError",
            "message": "A database error occurred",
            "path": str(request.url.path)
        }
    )


def pydantic_validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, PydanticValidationError):
        logger.error(f"Unexpected exception type in pydantic_validation_error_handler: {type(exc)}")
        raise exc

    logger.warning(
        "ValidationError: %s | Path: %s | Method: %s",
        _sanitize_for_log(str(exc.errors())),
        _sanitize_for_log(str(request.url.path)),
        request.method,
    )

    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Invalid input data",
            "details": errors,
            "path": str(request.url.path)
        }
    )


def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        "Unhandled exception: %s | Path: %s | Method: %s",
        _sanitize_for_log(str(exc)),
        _sanitize_for_log(str(request.url.path)),
        request.method,
    )

    if settings.is_development():
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": str(exc),
                "traceback": traceback.format_exc()
            }
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred"
            }
        )