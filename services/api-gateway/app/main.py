"""API Gateway for KnowledgeOps platform.

Routes requests to backend services, aggregates health, and logs all traffic.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from shared_core.errors import BaseApplicationError, application_error_handler
from shared_core.logging import setup_logging

from app.config import GatewaySettings
from app.routes.health import router as health_router
from app.routes.proxy import router as proxy_router

settings = GatewaySettings()
setup_logging(level=settings.LOG_LEVEL, service_name="api-gateway")

app = FastAPI(
    title="KnowledgeOps API Gateway",
    version="0.1.0",
    description="Central request router and health aggregator.",
)

app.add_exception_handler(BaseApplicationError, application_error_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    # Wildcard origins cannot be combined with credentials; these services
    # authenticate with bearer tokens, not cookies, so credentials are off
    # whenever the origin list is the permissive wildcard.
    allow_credentials="*" not in settings.cors_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["health"])
app.include_router(proxy_router, prefix="/api", tags=["proxy"])
