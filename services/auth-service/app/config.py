"""Auth service configuration."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "shared" / "python"))

from shared.config import BaseServiceSettings


class AuthSettings(BaseServiceSettings):
    """Configuration for the Auth Service.

    Inherits common fields from BaseServiceSettings and adds auth-specific
    JWT settings.

    Attributes:
        jwt_secret: Secret key for JWT token signing.
        jwt_algorithm: JWT signing algorithm.
        jwt_expiration_minutes: Token lifetime in minutes.
    """

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    jwt_issuer: str = "knowledgeops-auth"
    jwt_audience: str = "knowledgeops-api"
