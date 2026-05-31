"""Auth Service for KnowledgeOps platform.

Manages API keys, user sessions, and role-based access control.
"""

from fastapi import FastAPI

from app.routes import auth as auth_routes
from app.config import AuthSettings

settings = AuthSettings()

app = FastAPI(
    title="KnowledgeOps Auth Service",
    version="0.1.0",
    description="Authentication, API keys, and RBAC.",
)

app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service health."""
    return {"status": "healthy", "service": "auth-service"}
