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


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, AppException):
        logger.error(f"Unexpected exception type in app_exception_handler: {type(exc)}")
        raise exc
    
    logger.error(
        f"{exc.__class__.__name__}: {exc.message} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method}"
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "path": str(request.url.path)
        }
    )


async def integrity_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, IntegrityError):
        logger.error(f"Unexpected exception type in integrity_error_handler: {type(exc)}")
        raise exc
    
    error_message = str(exc.orig).lower()
    logger.error(
        f"IntegrityError: {error_message} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method}"
    )
    
    if "check_trip_dates" in error_message:
        message = "End date must be after start date"
        error_type = "InvalidDateRangeError"
    elif "check_accommodation_dates" in error_message:
        message = "Check-out date must be after check-in date"
        error_type = "InvalidDateRangeError"
    elif "unique" in error_message or "duplicate" in error_message:
        if "email" in error_message:
            message = "Email already registered"
        else:
            message = "Resource already exists"
        error_type = "DuplicateResourceError"
    elif "foreign key" in error_message or "violates foreign key" in error_message:
        message = "Referenced resource not found"
        error_type = "ForeignKeyError"
    elif "not null" in error_message or "null value" in error_message:
        match = re.search(r'column "(\w+)"', error_message)
        field = match.group(1) if match else "Field"
        message = f"{field} is required"
        error_type = "NotNullError"
    else:
        message = "Database constraint violation"
        error_type = "DatabaseConstraintError"
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": error_type,
            "message": message,
            "path": str(request.url.path)
        }
    )


async def sqlalchemy_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, SQLAlchemyError):
        logger.error(f"Unexpected exception type in sqlalchemy_error_handler: {type(exc)}")
        raise exc
    
    logger.error(
        f"SQLAlchemyError: {str(exc)} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method}",
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


async def pydantic_validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    if not isinstance(exc, PydanticValidationError):
        logger.error(f"Unexpected exception type in pydantic_validation_error_handler: {type(exc)}")
        raise exc
    
    logger.warning(
        f"ValidationError: {exc.errors()} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method}"
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


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(
        f"Unhandled exception: {str(exc)} | "
        f"Path: {request.url.path} | "
        f"Method: {request.method}"
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