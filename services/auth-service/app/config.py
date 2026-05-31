"""Auth service configuration."""

from pydantic_settings import BaseSettings


class AuthSettings(BaseSettings):
    """Configuration for the Auth Service.

    Attributes:
        database_url: PostgreSQL connection string.
        jwt_secret: Secret key for JWT token signing.
        jwt_algorithm: JWT signing algorithm.
        jwt_expiration_minutes: Token lifetime in minutes.
    """

    database_url: str = "postgresql://knowledgeops:knowledgeops@db:5432/knowledgeops"
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    model_config = {"env_file": ".env", "extra": "ignore"}
