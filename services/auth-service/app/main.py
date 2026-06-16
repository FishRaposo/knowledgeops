"""Auth Service for KnowledgeOps platform.

Manages API keys, user sessions, and role-based access control.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared.readiness import readiness_payload
from shared_core.errors import BaseApplicationError, application_error_handler
from shared_core.logging import setup_logging

from app.config import AuthSettings
from app.database import check_db
from app.routes import auth as auth_routes

settings = AuthSettings()
setup_logging(level=settings.LOG_LEVEL, service_name="auth-service")

app = FastAPI(
    title="KnowledgeOps Auth Service",
    version="0.1.0",
    description="Authentication, API keys, and RBAC.",
)

app.add_exception_handler(BaseApplicationError, application_error_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    # Bearer-token auth (no cookies); wildcard origins forbid credentials.
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service health."""
    return {"status": "healthy", "service": "auth-service"}


@app.get("/ready")
async def ready() -> dict[str, object]:
    """Readiness probe: re-checks the database with bounded backoff."""
    return await readiness_payload("auth-service", check_db)
