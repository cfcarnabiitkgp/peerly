"""
Configuration settings for Peerly application.
Uses Pydantic BaseSettings for environment variable management.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    app_name: str = "Peerly - Technical Manuscript Reviewer"
    app_version: str = "0.1.0"
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS Settings
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000"
    ]

    # OpenAI Configuration
    openai_api_key: str
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.2

    # Qdrant Configuration
    qdrant_url: str = "http://localhost:6333"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "technical_guidelines"

    # Agent Configuration
    max_parallel_agents: int = 3
    agent_timeout: int = 30

    # RAG Configuration
    use_rag: bool = True  # Enable/disable RAG (set USE_RAG=false to disable)
    use_semantic_cache: bool = False  # Enable/disable semantic caching for RAG queries

    # Railway-specific settings
    railway_environment: str | None = None  # Will be "production" on Railway
    railway_static_url: str | None = None
    railway_public_domain: str | None = None  # Backend's own domain (auto-provided by Railway)
    frontend_domain: str | None = None  # Frontend domain for CORS

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS origins including Railway frontend URL."""
        origins = self.cors_origins.copy() if isinstance(self.cors_origins, list) else [self.cors_origins]

        # Add Railway frontend URL if available
        if self.frontend_domain:
            origins.append(f"https://{self.frontend_domain}")

        return origins


# Global settings instance
settings = Settings()
