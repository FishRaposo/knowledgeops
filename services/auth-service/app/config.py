"""Auth service configuration."""

from shared_core.config import BaseAppConfig


class AuthSettings(BaseAppConfig):
    """Configuration for the Auth Service.

    Inherits common infrastructure fields from ``shared_core.config.BaseAppConfig``
    and adds auth-specific JWT settings.
    """

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    jwt_issuer: str = "knowledgeops-auth"
    jwt_audience: str = "knowledgeops-api"
