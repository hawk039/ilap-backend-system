from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models import User
from app.schemas.auth import (
    AuthResponse,
    ForgotPasswordRequest,
    LoginRequest,
    RefreshSessionRequest,
    RegisterRequest,
    ResetPasswordRequest,
    SessionResponse,
    VerifyEmailRequest,
)
from app.schemas.common import MessageResponse
from app.services import auth as auth_service
from app.services.rate_limit import enforce_rate_limit

router = APIRouter()


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthResponse:
    enforce_rate_limit(
        key=f"register:{request.client.host if request.client else 'unknown'}",
        limit=settings.register_rate_limit_per_minute,
        window_seconds=60,
    )
    return auth_service.register_user(
        db,
        full_name=payload.full_name,
        email=payload.email,
        password=payload.password.get_secret_value(),
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.client.host if request.client else None,
        settings=settings,
    )


@router.post("/login", response_model=AuthResponse)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthResponse:
    enforce_rate_limit(
        key=f"login:{payload.email.lower()}:{request.client.host if request.client else 'unknown'}",
        limit=settings.login_rate_limit_per_minute,
        window_seconds=60,
    )
    return auth_service.login_user(
        db,
        email=payload.email,
        password=payload.password.get_secret_value(),
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.client.host if request.client else None,
        settings=settings,
    )


@router.post("/refresh", response_model=AuthResponse)
def refresh(
    payload: RefreshSessionRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> AuthResponse:
    return auth_service.refresh_user_session(
        db,
        refresh_token=payload.refresh_token,
        settings=settings,
        user_agent=request.headers.get("User-Agent"),
        ip_address=request.client.host if request.client else None,
    )


@router.post("/logout", response_model=MessageResponse)
def logout(
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    auth_service.revoke_session(db, session=current.session, actor_id=current.user.id)
    return MessageResponse(message="Logout successful.")


@router.get("/session", response_model=SessionResponse)
def auth_session(current: CurrentUser = Depends(get_current_user)) -> SessionResponse:
    return auth_service.build_session_response(current.user)


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    payload: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> MessageResponse:
    enforce_rate_limit(
        key=f"forgot:{payload.email.lower()}:{request.client.host if request.client else 'unknown'}",
        limit=settings.forgot_password_rate_limit_per_hour,
        window_seconds=3600,
    )
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if user:
        auth_service.issue_password_reset_token(db, user=user, settings=settings)
    return MessageResponse(message="If the account exists, password reset instructions will be sent.")


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    auth_service.reset_password(db, token=payload.token, new_password=payload.password.get_secret_value())
    return MessageResponse(message="Password reset completed.")


@router.post("/verify-email", response_model=MessageResponse)
def verify_email(
    payload: VerifyEmailRequest,
    db: Session = Depends(get_db),
) -> MessageResponse:
    auth_service.verify_email(db, token=payload.token)
    return MessageResponse(message="Email verification completed.")
