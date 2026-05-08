import re

from pydantic import Field, SecretStr, field_validator

from app.schemas.common import APIModel, EmailValue


class RegisterRequest(APIModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailValue
    password: SecretStr = Field(min_length=12, max_length=128)

    _validate_password = field_validator("password")(lambda cls, value: _validate_password(value))


class LoginRequest(APIModel):
    email: EmailValue
    password: SecretStr = Field(min_length=12, max_length=128)


class RefreshSessionRequest(APIModel):
    refresh_token: str = Field(min_length=20, max_length=255)


class ForgotPasswordRequest(APIModel):
    email: EmailValue


class ResetPasswordRequest(APIModel):
    token: str = Field(min_length=20, max_length=255)
    password: SecretStr = Field(min_length=12, max_length=128)

    _validate_password = field_validator("password")(lambda cls, value: _validate_password(value))


class VerifyEmailRequest(APIModel):
    token: str = Field(min_length=20, max_length=255)


class ResendVerificationRequest(APIModel):
    email: EmailValue


class SessionTokens(APIModel):
    access_token: str
    refresh_token: str


class AuthUser(APIModel):
    id: str
    full_name: str
    email: EmailValue
    role: str
    email_verified_at: str | None = None


class AuthResponse(APIModel):
    user: AuthUser
    session: SessionTokens


class SessionResponse(APIModel):
    authenticated: bool
    user: AuthUser | None = None


def _validate_password(value: SecretStr) -> SecretStr:
    password = value.get_secret_value()
    if not re.search(r"[a-z]", password):
        raise ValueError("Password must include a lowercase letter.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("Password must include an uppercase letter.")
    if not re.search(r"\d", password):
        raise ValueError("Password must include a number.")
    if not re.search(r"[^A-Za-z0-9]", password):
        raise ValueError("Password must include a special character.")
    return value
