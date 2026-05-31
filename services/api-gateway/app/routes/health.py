"""Health check routes for the API Gateway."""

from datetime import datetime

from fastapi import APIRouter
from httpx import AsyncClient
from pydantic import BaseModel

from app.config import GatewaySettings

router = APIRouter()
settings = GatewaySettings()


class ServiceHealth(BaseModel):
    """Health status of a single service.

    Attributes:
        service: Service name.
        status: Health status string.
        response_time_ms: Response time in milliseconds.
    """

    service: str
    status: str
    response_time_ms: float


class AggregatedHealth(BaseModel):
    """Aggregated health response from all services.

    Attributes:
        status: Overall gateway health.
        timestamp: Check timestamp.
        services: Individual service health statuses.
    """

    status: str
    timestamp: datetime
    services: list[ServiceHealth]


@router.get("/health", response_model=AggregatedHealth)
async def health_check() -> AggregatedHealth:
    """Check health of all backend services and return aggregated status."""
    services_to_check: dict[str, str] = {
        "auth-service": settings.auth_service_url,
        "ingestion-service": settings.ingestion_service_url,
        "retrieval-service": settings.retrieval_service_url,
        "llm-gateway": settings.llm_gateway_url,
        "eval-service": settings.eval_service_url,
        "trace-service": settings.trace_service_url,
    }

    service_results: list[ServiceHealth] = []
    async with AsyncClient(timeout=5.0) as client:
        for name, url in services_to_check.items():
            start = datetime.now()
            try:
                response = await client.get(f"{url}/health")
                elapsed = (datetime.now() - start).total_seconds() * 1000
                service_results.append(
                    ServiceHealth(
                        service=name,
                        status="healthy" if response.status_code == 200 else "unhealthy",
                        response_time_ms=round(elapsed, 2),
                    )
                )
            except Exception:
                elapsed = (datetime.now() - start).total_seconds() * 1000
                service_results.append(
                    ServiceHealth(service=name, status="unhealthy", response_time_ms=round(elapsed, 2))
                )

    all_healthy = all(s.status == "healthy" for s in service_results)
    return AggregatedHealth(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.now(),
        services=service_results,
    )
