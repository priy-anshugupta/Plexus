"""
Plexus Backend — Application Configuration

Loads environment variables from .env and exposes them as typed settings
via Pydantic Settings. All database connection strings, API keys, and
feature flags are managed here.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Application ---
    app_name: str = "Plexus"
    app_env: str = "development"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # --- PostgreSQL ---
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "plexus"
    postgres_password: str = "plexuspassword"
    postgres_db: str = "plexus_db"

    @property
    def postgres_dsn(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # --- Neo4j ---
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "plexuspassword"

    # --- Qdrant ---
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # --- Redis ---
    redis_host: str = "localhost"
    redis_port: int = 6379

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}"

    # --- LLM Providers ---
    openai_api_key: str = ""
    anthropic_api_key: str = ""

    # --- GitHub App ---
    github_app_id: str = ""
    github_app_private_key_path: str = ""
    github_webhook_secret: str = ""


# Singleton instance — import this throughout the application
settings = Settings()
