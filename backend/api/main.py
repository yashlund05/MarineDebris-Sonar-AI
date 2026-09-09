"""FastAPI application factory, middleware, and exception handlers."""

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.api.routers import (
    datasets,
    detections,
    enhancement,
    inference,
    jobs,
    models,
    reports,
    sonar_enhancement,
    surveys,
    system,
    ws,
)
from contextlib import asynccontextmanager

from backend.config import get_settings
from backend.exceptions import AppException
from backend.logging_config import get_logger, setup_logging
from backend.database.session import get_async_engine
from backend.database.models import Base

settings = get_settings()
setup_logging(debug=settings.DEBUG)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    # Ensure storage and data directories exist
    import os
    os.makedirs(settings.storage_root_path, exist_ok=True)
    os.makedirs("./data", exist_ok=True)

    # Initialize database tables automatically only if permitted (development / SQLite standalone)
    # Production PostgreSQL deployments must use Alembic migrations (alembic upgrade head)
    should_auto_create = settings.AUTO_CREATE_TABLES or (
        settings.ENVIRONMENT == "development" and "sqlite" in settings.async_database_url
    )
    if should_auto_create:
        try:
            engine = get_async_engine()
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables initialized successfully via AUTO_CREATE_TABLES.")
        except Exception as e:
            logger.warning("Database table auto-creation skipped or deferred: %s", str(e))
    else:
        logger.info("AUTO_CREATE_TABLES disabled. Schema migrations managed by Alembic.")

    yield

    # Clean up on shutdown
    try:
        await get_async_engine().dispose()
    except Exception:
        pass


def create_app() -> FastAPI:
    """Create and configure FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=settings.PROJECT_DESCRIPTION,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request ID and Request Logging Middleware
    @app.middleware("http")
    async def request_middleware(request: Request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        start_time = time.time()

        response = await call_next(request)

        duration_ms = round((time.time() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time-Ms"] = str(duration_ms)
        return response

    # Exception Handlers
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": exc.error_code,
                    "message": exc.message,
                    "details": exc.details,
                },
                "meta": {
                    "request_id": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed.",
                    "details": {"errors": exc.errors()},
                },
                "meta": {
                    "request_id": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": str(exc.detail),
                    "details": {},
                },
                "meta": {
                    "request_id": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        logger.exception("Unhandled server exception: %s", str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected internal server error occurred.",
                    "details": {},
                },
                "meta": {
                    "request_id": request_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            },
        )

    # Include API Routers
    app.include_router(datasets.router, prefix=settings.API_V1_STR)
    app.include_router(system.router, prefix=settings.API_V1_STR)
    app.include_router(surveys.router, prefix=settings.API_V1_STR)
    app.include_router(jobs.router, prefix=settings.API_V1_STR)
    app.include_router(ws.router, prefix=settings.API_V1_STR)
    app.include_router(detections.router, prefix=settings.API_V1_STR)
    app.include_router(reports.router, prefix=settings.API_V1_STR)
    app.include_router(models.router, prefix=settings.API_V1_STR)
    app.include_router(inference.router, prefix=settings.API_V1_STR)
    app.include_router(enhancement.router, prefix=settings.API_V1_STR)
    app.include_router(sonar_enhancement.router, prefix=f"{settings.API_V1_STR}/sonar")

    # Convenience root health redirect / root endpoint
    @app.get("/health", tags=["System & Health"])
    async def root_health():
        return {"status": "ok", "service": settings.PROJECT_NAME, "version": settings.VERSION}

    return app


app = create_app()
