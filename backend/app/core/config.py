from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central runtime configuration loaded from environment variables.

    Keeping these values in one settings object makes deployment-specific behavior
    explicit and avoids hard-coding runtime assumptions across the codebase.
    """

    app_name: str = "Intelligent DataOps Platform"
    api_prefix: str = "/api/v1"
    environment: str = "development"
    database_url: str = "sqlite:///./daos.db"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    enforce_security_headers: bool = True
    auth_enabled: bool = False
    api_keys_csv: str = ""
    llm_base_url: str = "http://localhost:1234/v1"
    llm_model: str = "local-model"
    llm_api_key: str = ""
    llm_timeout_seconds: float = 30.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
