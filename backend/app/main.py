import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.auth import router as auth_router
from app.api.v1.applications import router as apps_router
from app.api.v1.emails import router as emails_router
from app.api.v1.followups import router as followups_router
from app.api.v1.settings import router as settings_router
from app.api.v1.dashboard import router as dashboard_router
from app.core.logging import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database tables exist
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.log_event("db_init_warning", {"error": str(e)}, level="warning")
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    logger.log_event("app_started", {"project": settings.PROJECT_NAME, "version": settings.VERSION})
    yield
    logger.log_event("app_shutdown", {})

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Error Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.log_event("unhandled_error", {
        "url": str(request.url),
        "method": request.method,
        "error": str(exc)
    }, level="error")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "An internal server error occurred.",
            "error_code": "INTERNAL_SERVER_ERROR"
        }
    )

# Include API Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(apps_router, prefix=settings.API_V1_STR)
app.include_router(emails_router, prefix=settings.API_V1_STR)
app.include_router(followups_router, prefix=settings.API_V1_STR)
app.include_router(settings_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs": "/docs"
    }
