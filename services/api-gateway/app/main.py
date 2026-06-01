"""API Gateway for KnowledgeOps platform.

Routes requests to backend services, aggregates health, and logs all traffic.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import GatewaySettings
from app.routes.health import router as health_router
from app.routes.proxy import router as proxy_router

settings = GatewaySettings()

app = FastAPI(
    title="KnowledgeOps API Gateway",
    version="0.1.0",
    description="Central request router and health aggregator.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, tags=["health"])
app.include_router(proxy_router, prefix="/api", tags=["proxy"])
