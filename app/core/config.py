import json
import os
from functools import lru_cache

from pydantic import BaseModel, Field


class Settings(BaseModel):

    app_name: str = "ILAP Platform Backend"
    app_version: str = "1.0.0"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    debug: bool = False
    auto_create_schema: bool = True

    database_url: str = "sqlite:///./storage/ilap.db"
    sync_database_url: str | None = None

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30

    password_reset_ttl_minutes: int = 30
    email_verification_ttl_hours: int = 24

    ai_service_base_url: str = "http://127.0.0.1:9000"
    ai_service_timeout_seconds: int = 20
    ai_stub_mode: bool = True

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    login_rate_limit_per_minute: int = 10
    register_rate_limit_per_minute: int = 10
    forgot_password_rate_limit_per_hour: int = 5
    ask_rate_limit_per_minute: int = 30

    admin_bootstrap_email: str = "admin@ilap.local"
    admin_bootstrap_password: str = "ChangeMe123!"

    @classmethod
    def from_env(cls) -> "Settings":
        cors_origins = os.getenv("CORS_ORIGINS")
        parsed_origins = ["http://localhost:3000"]
        if cors_origins:
            try:
                loaded = json.loads(cors_origins)
                if isinstance(loaded, list):
                    parsed_origins = [str(item) for item in loaded]
            except json.JSONDecodeError:
                parsed_origins = [item.strip() for item in cors_origins.split(",") if item.strip()]
        return cls(
            app_name=os.getenv("APP_NAME", cls.model_fields["app_name"].default),
            app_version=os.getenv("APP_VERSION", cls.model_fields["app_version"].default),
            environment=os.getenv("ENVIRONMENT", cls.model_fields["environment"].default),
            api_prefix=os.getenv("API_PREFIX", cls.model_fields["api_prefix"].default),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            auto_create_schema=os.getenv("AUTO_CREATE_SCHEMA", "true").lower() == "true",
            database_url=os.getenv("DATABASE_URL", cls.model_fields["database_url"].default),
            sync_database_url=os.getenv("SYNC_DATABASE_URL", None),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", cls.model_fields["jwt_secret_key"].default),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", cls.model_fields["jwt_algorithm"].default),
            access_token_ttl_minutes=int(os.getenv("ACCESS_TOKEN_TTL_MINUTES", "15")),
            refresh_token_ttl_days=int(os.getenv("REFRESH_TOKEN_TTL_DAYS", "30")),
            password_reset_ttl_minutes=int(os.getenv("PASSWORD_RESET_TTL_MINUTES", "30")),
            email_verification_ttl_hours=int(os.getenv("EMAIL_VERIFICATION_TTL_HOURS", "24")),
            ai_service_base_url=os.getenv(
                "AI_SERVICE_BASE_URL",
                cls.model_fields["ai_service_base_url"].default,
            ),
            ai_service_timeout_seconds=int(os.getenv("AI_SERVICE_TIMEOUT_SECONDS", "20")),
            ai_stub_mode=os.getenv("AI_STUB_MODE", "true").lower() == "true",
            cors_origins=parsed_origins,
            login_rate_limit_per_minute=int(os.getenv("LOGIN_RATE_LIMIT_PER_MINUTE", "10")),
            register_rate_limit_per_minute=int(os.getenv("REGISTER_RATE_LIMIT_PER_MINUTE", "10")),
            forgot_password_rate_limit_per_hour=int(os.getenv("FORGOT_PASSWORD_RATE_LIMIT_PER_HOUR", "5")),
            ask_rate_limit_per_minute=int(os.getenv("ASK_RATE_LIMIT_PER_MINUTE", "30")),
            admin_bootstrap_email=os.getenv(
                "ADMIN_BOOTSTRAP_EMAIL",
                cls.model_fields["admin_bootstrap_email"].default,
            ),
            admin_bootstrap_password=os.getenv(
                "ADMIN_BOOTSTRAP_PASSWORD",
                cls.model_fields["admin_bootstrap_password"].default,
            ),
        )

    @property
    def resolved_sync_database_url(self) -> str:
        if self.sync_database_url:
            return self.sync_database_url
        if self.database_url.startswith("postgresql+psycopg://"):
            return self.database_url
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
