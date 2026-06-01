"""Proxy routes that forward requests to backend services."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from httpx import AsyncClient

from app.config import GatewaySettings
from app.routes.health import health_check

router = APIRouter()
settings = GatewaySettings()

SERVICE_MAP: dict[str, str] = {
    "documents": settings.ingestion_service_url,
    "ingest": settings.ingestion_service_url,
    "query": settings.retrieval_service_url,
    "retrieve": settings.retrieval_service_url,
    "auth": settings.auth_service_url,
    "evals": settings.eval_service_url,
    "eval": settings.eval_service_url,
    "traces": settings.trace_service_url,
}


async def verify_request_auth(request: Request) -> dict[str, Any]:
    """Dependency that validates JWT Bearer token via the auth service."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth_header.removeprefix("Bearer ").strip()
    if settings.allow_dev_auth and token == settings.demo_token:
        return {
            "valid": True,
            "user_id": "dev-admin",
            "email": "admin@knowledgeops.local",
            "role": "admin",
        }

    async with AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(
                f"{settings.auth_service_url}/auth/verify",
                headers={"Authorization": auth_header},
            )
            if response.status_code != 200:
                raise HTTPException(status_code=401, detail="Invalid or expired token")
            return response.json()
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=502, detail="Auth service unavailable")


@router.api_route("/documents/upload", methods=["POST"])
async def proxy_document_upload(
    request: Request, _auth: dict[str, Any] = Depends(verify_request_auth)
) -> dict[str, Any]:
    """Proxy document upload to the ingestion service."""
    base_url = settings.ingestion_service_url
    content_type = request.headers.get("content-type", "")
    async with AsyncClient(timeout=60.0) as client:
        if "multipart/form-data" in content_type:
            form = await request.form()
            files = {key: (form[key].filename, await form[key].read(), form[key].content_type) for key in form}
            response = await client.post(f"{base_url}/ingest/upload", files=files)
        else:
            body = await request.body()
            response = await client.post(f"{base_url}/ingest/upload", content=body)

    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return _envelope(response.json(), "document")


@router.api_route("/documents", methods=["GET"])
async def proxy_list_documents(
    request: Request, _auth: dict[str, Any] = Depends(verify_request_auth)
) -> dict[str, Any]:
    """Proxy document list to the ingestion service."""
    async with AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{settings.ingestion_service_url}/ingest/documents")
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return _envelope(response.json(), "documents")


@router.api_route("/query", methods=["POST"])
async def proxy_query(
    request: Request, _auth: dict[str, Any] = Depends(verify_request_auth)
) -> dict[str, Any]:
    """Proxy query to the retrieval service."""
    body = await request.json()
    async with AsyncClient(timeout=30.0) as client:
        response = await client.post(f"{settings.retrieval_service_url}/retrieve/query", json=body)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.api_route("/evals/run", methods=["POST"])
async def proxy_eval_run(
    request: Request, _auth: dict[str, Any] = Depends(verify_request_auth)
) -> dict[str, Any]:
    """Proxy eval run to the eval service."""
    body = await request.json()
    async with AsyncClient(timeout=120.0) as client:
        response = await client.post(f"{settings.eval_service_url}/eval/run", json=body)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return _envelope(response.json(), "eval_run")


@router.api_route("/evals", methods=["GET"])
async def proxy_list_evals(
    request: Request, _auth: dict[str, Any] = Depends(verify_request_auth)
) -> dict[str, Any]:
    """Proxy eval list to the eval service."""
    async with AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{settings.eval_service_url}/eval/runs")
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return _envelope(response.json(), "evals")


@router.api_route("/traces", methods=["GET"])
async def proxy_list_traces(
    request: Request, _auth: dict[str, Any] = Depends(verify_request_auth)
) -> dict[str, Any]:
    """Proxy trace list to the trace service."""
    async with AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{settings.trace_service_url}/traces")
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return _envelope(response.json(), "traces")


@router.api_route("/costs", methods=["GET"])
async def proxy_costs(
    request: Request, _auth: dict[str, Any] = Depends(verify_request_auth)
) -> dict[str, Any]:
    """Proxy cost summary from the trace service."""
    async with AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{settings.trace_service_url}/traces/costs")
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.api_route("/admin/users", methods=["GET"])
async def proxy_admin_users(
    request: Request, auth: dict[str, Any] = Depends(verify_request_auth)
) -> dict[str, Any]:
    """Proxy admin user list to the auth service."""
    if auth.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    if settings.allow_dev_auth and auth.get("user_id") == "dev-admin":
        return {
            "users": [
                {
                    "id": "dev-admin",
                    "email": "admin@knowledgeops.local",
                    "name": "Admin User",
                    "role": "admin",
                    "created_at": "2026-01-01T00:00:00Z",
                }
            ]
        }
    async with AsyncClient(timeout=10.0) as client:
        response = await client.get(
            f"{settings.auth_service_url}/auth/users",
            headers={"X-User-Role": str(auth.get("role", ""))},
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return _envelope(response.json(), "users")


@router.api_route("/admin/health", methods=["GET"])
async def proxy_admin_health(
    request: Request, auth: dict[str, Any] = Depends(verify_request_auth)
) -> dict[str, Any]:
    """Return admin service health overview."""
    if auth.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    health = await health_check()
    return health.model_dump(mode="json")


@router.api_route("/admin/keys", methods=["POST"])
async def proxy_admin_create_key(
    request: Request, auth: dict[str, Any] = Depends(verify_request_auth)
) -> dict[str, Any]:
    """Create an API key through auth service or deterministic dev mode."""
    if auth.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    body = await request.json()
    if settings.allow_dev_auth and auth.get("user_id") == "dev-admin":
        name = str(body.get("name", "Demo key"))
        return {
            "id": f"dev-key-{name.lower().replace(' ', '-')}",
            "name": name,
            "key": "ko_dev_mock_key",
            "created_at": "2026-01-01T00:00:00Z",
        }
    async with AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{settings.auth_service_url}/auth/keys",
            json=body,
            headers={"X-User-Role": str(auth.get("role", ""))},
        )
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.api_route("/alerts", methods=["GET"])
async def proxy_alerts(
    request: Request, _auth: dict[str, Any] = Depends(verify_request_auth)
) -> dict[str, Any]:
    """Proxy budget and service-failure alerts from trace service."""
    params = dict(request.query_params)
    params.setdefault("budget_limit_usd", str(settings.cost_budget_limit_usd))
    async with AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{settings.trace_service_url}/alerts", params=params)
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return response.json()


@router.api_route("/evals/runs", methods=["GET"])
async def proxy_eval_runs(
    request: Request, _auth: dict[str, Any] = Depends(verify_request_auth)
) -> dict[str, Any]:
    """Proxy eval runs list to the eval service."""
    async with AsyncClient(timeout=10.0) as client:
        response = await client.get(f"{settings.eval_service_url}/eval/runs")
    if response.status_code >= 400:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    return _envelope(response.json(), "evals")


def _envelope(payload: Any, collection_key: str) -> dict[str, Any]:
    """Normalize raw service arrays into stable gateway envelopes."""
    if isinstance(payload, dict) and collection_key in payload:
        return payload
    if isinstance(payload, list):
        return {collection_key: payload}
    if payload is None:
        return {collection_key: [] if collection_key.endswith("s") else None}
    return {collection_key: payload}
