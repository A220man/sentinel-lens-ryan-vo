"""Configuration and environment settings for Sentinel Lens."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Sentinel Lens"
    app_version: str = "1.0.0"
    environment: str = Field(default="development", description="Environment mode: development, testing, production")
    demo_mode: bool = Field(default=True, description="Enables local demo mode strictly on localhost")

    app_host: str = "127.0.0.1"
    app_port: int = 8000
    database_url: str = "sqlite:///./sentinel_lens.db"

    # OIDC & Keycloak Configuration
    oidc_issuer_url: str = "http://127.0.0.1:8080/realms/sentinel-lens"
    oidc_client_id: str = "sentinel-lens-app"
    oidc_audience: str = "sentinel-lens-api"
    oidc_client_secret: str = ""
    oidc_jwks_uri: str = ""

    # LLM Settings - LLM_API_KEY is the single secret credential
    llm_api_key: str = Field(default="", description="Operator provided LLM key; strictly server-side")
    llm_provider: str = Field(default="openai-compatible", description="Provider adapter: openai-compatible, anthropic, gemini, ollama")
    llm_model: str = Field(default="gpt-4o-mini", description="Configurable model name")
    llm_base_url: str = Field(default="https://api.openai.com/v1", description="Configurable API endpoint")
    llm_timeout_seconds: float = 12.0

    # Test Runner & Session Limits
    default_target: str = "web"
    device_pool_size: int = 8
    step_timeout_seconds: float = 30.0
    max_trace_steps: int = 500

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in {"development", "testing", "production"}:
            return "development"
        return clean

    def check_production_safety(self) -> None:
        """Enforces that demo mode is never enabled in a production environment."""
        if self.environment == "production" and self.demo_mode:
            raise RuntimeError(
                "Security policy violation: DEMO_MODE cannot be enabled when ENVIRONMENT=production. "
                "Disable DEMO_MODE and configure an authoritative OIDC Identity Provider."
            )


settings = Settings()
