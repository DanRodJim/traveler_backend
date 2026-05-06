from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from pydantic import ValidationError as PydanticValidationError
import logging
from contextlib import asynccontextmanager

from app.routers import auth, dashboard, users, trips, activities, flights, accommodations, expenses
from app.database.db import engine, Base
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.logging_config import setup_logging
from app.middleware.error_handler import (
    app_exception_handler,
    integrity_error_handler,
    sqlalchemy_error_handler,
    pydantic_validation_error_handler,
    generic_exception_handler
)

setup_logging(log_level="INFO" if settings.is_production() else "DEBUG")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Startup
    logger.info(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} starting...")
    
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")
    
    logger.info(f"Environment: {settings.ENV}")
    
    if settings.is_development():
        logger.info(f"API Docs: http://localhost:8000/api/docs")
        logger.info("Development mode - Debug enabled")
    elif settings.is_production():
        logger.info("Production mode - Optimized for performance")
    
    logger.info(f"{settings.PROJECT_NAME} started successfully!")
    
    yield
    
    # Shutdown
    logger.info("Application shutting down...")
    logger.info("Goodbye!")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for colaborative travel planner",
    version=settings.VERSION,
    docs_url="/api/docs" if settings.is_development() else None,
    redoc_url="/api/redoc" if settings.is_development() else None,
    lifespan=lifespan
)

# Exception handlers
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(IntegrityError, integrity_error_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_error_handler)
app.add_exception_handler(PydanticValidationError, pydantic_validation_error_handler)
app.add_exception_handler(Exception, generic_exception_handler)

logger.info("Exception handlers registered")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS + [settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(trips.router)
app.include_router(activities.router)
app.include_router(flights.router)
app.include_router(accommodations.router)
app.include_router(expenses.router)
app.include_router(dashboard.router)

logger.info("Routers registered")

# Health check
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "environment": settings.ENV,
        "version": settings.VERSION
    }


@app.get("/")
async def root():
    return {
        "message": f"{settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": "/api/docs" if settings.is_development() else None,
        "health": "/health"
    }