"""Auth service API routes."""

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import (
    create_access_token,
    generate_api_key,
    hash_api_key,
    verify_token,
)
from app.database import get_db
from app.models import ApiKeyModel, UserModel

from shared.models import User

router = APIRouter()


class TokenRequest(BaseModel):
    """Request to exchange an API key for a JWT token.

    Attributes:
        api_key: The API key to exchange.
    """

    api_key: str = Field(description="API key to exchange for a JWT")


class ApiKeyCreate(BaseModel):
    """Request to create a new API key.

    Attributes:
        name: Human-readable name for the key.
    """

    name: str = Field(description="Key name")
    user_email: str = Field(default="admin@example.com", description="Owner email")
    role: str = Field(default="admin", description="Owner role")


class ApiKeyResponse(BaseModel):
    """API key creation response.

    Attributes:
        id: Key identifier.
        name: Key name.
        key: The raw API key (shown only once).
        created_at: Creation timestamp.
    """

    id: str
    name: str
    key: str
    created_at: str


@router.post("/token")
async def exchange_token(
    request: TokenRequest, db: AsyncSession = Depends(get_db)
) -> dict[str, Any]:
    """Exchange an API key for a JWT access token."""
    key_hash = hash_api_key(request.api_key)

    result = await db.execute(
        select(ApiKeyModel).where(ApiKeyModel.key_hash == key_hash)
    )
    api_key_record = result.scalar_one_or_none()

    if api_key_record is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    api_key_record.last_used_at = datetime.now(timezone.utc)
    await db.commit()

    user_result = await db.execute(
        select(UserModel).where(UserModel.id == api_key_record.user_id)
    )
    user = user_result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return create_access_token(
        user_id=UUID(user.id),
        email=user.email,
        role=user.role,
    ).model_dump()


@router.get("/me")
async def get_current_user(request: Request) -> User:
    """Get the current user from the JWT bearer token."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth_header[len("Bearer "):]
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return User(
        id=payload.user_id,
        email=payload.email,
        name="User",
        role=payload.role,
    )


@router.get("/verify")
async def verify_token_endpoint(request: Request) -> dict[str, Any]:
    """Verify a JWT bearer token and return the payload."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth_header[len("Bearer "):]
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {
        "valid": True,
        "user_id": payload.user_id,
        "email": payload.email,
        "role": payload.role,
    }


@router.post("/keys")
async def create_api_key(
    request: ApiKeyCreate,
    x_user_role: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> ApiKeyResponse:
    """Create a new API key."""
    if x_user_role is not None and x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create API keys")
    user_result = await db.execute(select(UserModel).where(UserModel.email == request.user_email))
    user = user_result.scalar_one_or_none()
    if user is None:
        user = UserModel(email=request.user_email, name=request.user_email.split("@")[0], role=request.role)
        db.add(user)
        await db.flush()

    raw_key = generate_api_key()
    hashed = hash_api_key(raw_key)
    api_key_record = ApiKeyModel(
        name=request.name,
        key_hash=hashed,
        user_id=user.id,
    )
    db.add(api_key_record)
    await db.commit()
    await db.refresh(api_key_record)
    return ApiKeyResponse(
        id=str(api_key_record.id),
        name=request.name,
        key=raw_key,
        created_at=api_key_record.created_at.isoformat() if api_key_record.created_at else datetime.now(timezone.utc).isoformat(),
    )


@router.get("/keys")
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """List API keys for the current user (masked)."""
    result = await db.execute(select(ApiKeyModel))
    keys = result.scalars().all()
    return [
        {
            "id": str(key.id),
            "name": key.name,
            "key_prefix": key.key_hash[:8] if key.key_hash else "unknown",
            "is_active": True,
            "created_at": key.created_at.isoformat() if key.created_at else "",
        }
        for key in keys
    ]


@router.delete("/keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Revoke an API key."""
    from sqlalchemy import delete
    from uuid import UUID as UUIDType
    await db.execute(delete(ApiKeyModel).where(ApiKeyModel.id == UUIDType(key_id)))
    await db.commit()
    return {"message": f"Key {key_id} revoked"}


@router.get("/users")
async def list_users(
    x_user_role: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
) -> list[User]:
    """List all users (admin only)."""
    if x_user_role is not None and x_user_role != "admin":
        raise HTTPException(status_code=403, detail="Only admins can list users")
    result = await db.execute(select(UserModel))
    users = result.scalars().all()
    return [
        User(
            id=user.id,
            email=user.email,
            name=user.name or "User",
            role=user.role,
        )
        for user in users
    ]


@router.get("/rbac/check")
async def check_rbac(role: str, required_role: str) -> dict[str, Any]:
    """Check whether a role satisfies a required RBAC level."""
    from app.auth import check_permission

    return {
        "role": role,
        "required_role": required_role,
        "allowed": check_permission(role, required_role),
    }
