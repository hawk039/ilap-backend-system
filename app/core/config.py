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
    auto_create_schema: bool = False
    seed_reference_data: bool = True
    enable_admin_bootstrap: bool = False
    docs_enabled: bool = True

    database_url: str = "sqlite:///./storage/ilap.db"
    sync_database_url: str | None = None

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    require_verified_email: bool = False

    password_reset_ttl_minutes: int = 30
    email_verification_ttl_hours: int = 24

    ai_service_base_url: str = "https://ilap-backend.onrender.com"
    ai_service_timeout_seconds: int = 20
    ai_stub_mode: bool = True

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    login_rate_limit_per_minute: int = 10
    register_rate_limit_per_minute: int = 10
    forgot_password_rate_limit_per_hour: int = 5
    ask_rate_limit_per_minute: int = 30

    admin_bootstrap_email: str = "admin@ilap.local"
    admin_bootstrap_password: str = "ChangeMe123!"
    resend_api_key: str | None = None
    auth_email_from: str | None = None
    email_verification_url_template: str | None = None
    password_reset_url_template: str | None = None
    upstash_redis_rest_url: str | None = None
    upstash_redis_rest_token: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        settings = cls(
            app_name=os.getenv("APP_NAME", cls.model_fields["app_name"].default),
            app_version=os.getenv("APP_VERSION", cls.model_fields["app_version"].default),
            environment=os.getenv("ENVIRONMENT", cls.model_fields["environment"].default),
            api_prefix=os.getenv("API_PREFIX", cls.model_fields["api_prefix"].default),
            debug=_env_bool("DEBUG", False),
            auto_create_schema=_env_bool("AUTO_CREATE_SCHEMA", cls.model_fields["auto_create_schema"].default),
            seed_reference_data=_env_bool("SEED_REFERENCE_DATA", cls.model_fields["seed_reference_data"].default),
            enable_admin_bootstrap=_env_bool(
                "ENABLE_ADMIN_BOOTSTRAP",
                cls.model_fields["enable_admin_bootstrap"].default,
            ),
            docs_enabled=_env_bool("DOCS_ENABLED", cls.model_fields["docs_enabled"].default),
            database_url=os.getenv("DATABASE_URL", cls.model_fields["database_url"].default),
            sync_database_url=os.getenv("SYNC_DATABASE_URL", None),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", cls.model_fields["jwt_secret_key"].default),
            jwt_algorithm=os.getenv("JWT_ALGORITHM", cls.model_fields["jwt_algorithm"].default),
            access_token_ttl_minutes=_env_int("ACCESS_TOKEN_TTL_MINUTES", 15),
            refresh_token_ttl_days=_env_int("REFRESH_TOKEN_TTL_DAYS", 30),
            require_verified_email=_env_bool(
                "REQUIRE_VERIFIED_EMAIL",
                cls.model_fields["require_verified_email"].default,
            ),
            password_reset_ttl_minutes=_env_int("PASSWORD_RESET_TTL_MINUTES", 30),
            email_verification_ttl_hours=_env_int("EMAIL_VERIFICATION_TTL_HOURS", 24),
            ai_service_base_url=os.getenv(
                "AI_SERVICE_BASE_URL",
                cls.model_fields["ai_service_base_url"].default,
            ),
            ai_service_timeout_seconds=_env_int("AI_SERVICE_TIMEOUT_SECONDS", 20),
            ai_stub_mode=_env_bool("AI_STUB_MODE", True),
            cors_origins=_env_list("CORS_ORIGINS", ["http://localhost:3000"]),
            login_rate_limit_per_minute=_env_int("LOGIN_RATE_LIMIT_PER_MINUTE", 10),
            register_rate_limit_per_minute=_env_int("REGISTER_RATE_LIMIT_PER_MINUTE", 10),
            forgot_password_rate_limit_per_hour=_env_int("FORGOT_PASSWORD_RATE_LIMIT_PER_HOUR", 5),
            ask_rate_limit_per_minute=_env_int("ASK_RATE_LIMIT_PER_MINUTE", 30),
            admin_bootstrap_email=os.getenv(
                "ADMIN_BOOTSTRAP_EMAIL",
                cls.model_fields["admin_bootstrap_email"].default,
            ),
            admin_bootstrap_password=os.getenv(
                "ADMIN_BOOTSTRAP_PASSWORD",
                cls.model_fields["admin_bootstrap_password"].default,
            ),
            resend_api_key=os.getenv("RESEND_API_KEY"),
            auth_email_from=os.getenv("AUTH_EMAIL_FROM"),
            email_verification_url_template=os.getenv("EMAIL_VERIFICATION_URL_TEMPLATE"),
            password_reset_url_template=os.getenv("PASSWORD_RESET_URL_TEMPLATE"),
            upstash_redis_rest_url=os.getenv("UPSTASH_REDIS_REST_URL"),
            upstash_redis_rest_token=os.getenv("UPSTASH_REDIS_REST_TOKEN"),
        )
        settings.validate_runtime()
        return settings

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def resolved_sync_database_url(self) -> str:
        if self.sync_database_url:
            return _normalize_database_url(self.sync_database_url)
        return self.resolved_database_url

    @property
    def resolved_database_url(self) -> str:
        return _normalize_database_url(self.database_url)

    def validate_runtime(self) -> None:
        if not self.cors_origins:
            raise ValueError("CORS_ORIGINS must contain at least one origin.")
        if bool(self.resend_api_key) != bool(self.auth_email_from):
            raise ValueError("RESEND_API_KEY and AUTH_EMAIL_FROM must either both be set or both be empty.")
        if bool(self.upstash_redis_rest_url) != bool(self.upstash_redis_rest_token):
            raise ValueError(
                "UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN must either both be set or both be empty."
            )
        if self.is_production:
            if self.debug:
                raise ValueError("DEBUG must be false in production.")
            if self.jwt_secret_key == "change-me-in-production":
                raise ValueError("JWT_SECRET_KEY must be set to a non-default value in production.")
            if len(self.jwt_secret_key) < 32:
                raise ValueError("JWT_SECRET_KEY must be at least 32 characters long in production.")
            if self.resolved_database_url.startswith("sqlite"):
                raise ValueError("Production deployments must use PostgreSQL, not SQLite.")
            if self.enable_admin_bootstrap and self.admin_bootstrap_password == "ChangeMe123!":
                raise ValueError(
                    "ADMIN_BOOTSTRAP_PASSWORD must be changed before enabling admin bootstrap in production."
                )
            if self.require_verified_email and (not self.resend_api_key or not self.auth_email_from):
                raise ValueError(
                    "Production email verification requires RESEND_API_KEY and AUTH_EMAIL_FROM to be configured."
                )


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _env_list(name: str, default: list[str]) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return list(default)
    try:
        loaded = json.loads(value)
        if isinstance(loaded, list):
            return [str(item) for item in loaded if str(item).strip()]
    except json.JSONDecodeError:
        pass
    return [item.strip() for item in value.split(",") if item.strip()]


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


@lru_cache
def get_settings() -> Settings:
    return Settings.from_env()
