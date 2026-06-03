"""Auth Service for KnowledgeOps platform.

Manages API keys, user sessions, and role-based access control.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth as auth_routes
from app.config import AuthSettings

settings = AuthSettings()

app = FastAPI(
    title="KnowledgeOps Auth Service",
    version="0.1.0",
    description="Authentication, API keys, and RBAC.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router, prefix="/auth", tags=["auth"])


@app.get("/health")
async def health() -> dict[str, str]:
    """Return service health."""
    return {"status": "healthy", "service": "auth-service"}
