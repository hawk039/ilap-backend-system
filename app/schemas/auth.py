from pydantic import Field, SecretStr

from app.schemas.common import APIModel, EmailValue


class RegisterRequest(APIModel):
    full_name: str = Field(min_length=2, max_length=120)
    email: EmailValue
    password: SecretStr = Field(min_length=8, max_length=128)


class LoginRequest(APIModel):
    email: EmailValue
    password: SecretStr = Field(min_length=8, max_length=128)


class RefreshSessionRequest(APIModel):
    refresh_token: str = Field(min_length=20, max_length=255)


class ForgotPasswordRequest(APIModel):
    email: EmailValue


class ResetPasswordRequest(APIModel):
    token: str = Field(min_length=20, max_length=255)
    password: SecretStr = Field(min_length=8, max_length=128)


class VerifyEmailRequest(APIModel):
    token: str = Field(min_length=20, max_length=255)


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
