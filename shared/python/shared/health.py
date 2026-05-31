"""Health check models for KnowledgeOps services."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class HealthStatus(str, Enum):
    """Service health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthResponse(BaseModel):
    """Standard health check response.

    Attributes:
        status: Overall health status.
        service: Name of the service reporting health.
        version: Service version string.
        timestamp: Time of the health check.
        dependencies: Health status of upstream dependencies.
        metadata: Additional service-specific metadata.
    """

    status: HealthStatus = Field(description="Overall health status")
    service: str = Field(description="Service name")
    version: str = Field(default="0.1.0", description="Service version")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    dependencies: dict[str, HealthStatus] = Field(
        default_factory=dict, description="Upstream dependency statuses"
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
