from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import conflict, not_found, unauthorized
from app.core.security import create_access_token, hash_password, verify_password
from app.models import EmailVerificationToken, PasswordResetToken, User, UserSession
from app.schemas.auth import AuthResponse, AuthUser, SessionResponse, SessionTokens
from app.schemas.users import NotificationPreferences, UserProfile
from app.services.audit import write_audit_log


def now_utc() -> datetime:
    return datetime.now(UTC)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_opaque_token(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def build_auth_user(user: User) -> AuthUser:
    return AuthUser(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        email_verified_at=user.email_verified_at.isoformat() if user.email_verified_at else None,
    )


def build_profile(user: User) -> UserProfile:
    return UserProfile(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        role=user.role,
        avatar_url=user.avatar_url,
        organization=user.organization,
        jurisdiction=user.jurisdiction,
        preferred_practice_areas=user.preferred_practice_areas or [],
        notification_preferences=NotificationPreferences.model_validate(user.notification_preferences or {}),
        created_at=user.created_at,
        updated_at=user.updated_at,
        email_verified_at=user.email_verified_at,
    )


def create_session(
    db: Session,
    *,
    user: User,
    settings: Settings,
    user_agent: str | None,
    ip_address: str | None,
    existing_session: UserSession | None = None,
) -> SessionTokens:
    raw_refresh_token = generate_opaque_token("refresh")
    expires_at = now_utc() + timedelta(days=settings.refresh_token_ttl_days)
    if existing_session is None:
        session = UserSession(
            user_id=user.id,
            refresh_token_hash=hash_token(raw_refresh_token),
            user_agent=user_agent,
            ip_address=ip_address,
            expires_at=expires_at,
            created_at=now_utc(),
        )
        db.add(session)
        db.flush()
    else:
        existing_session.refresh_token_hash = hash_token(raw_refresh_token)
        existing_session.expires_at = expires_at
        existing_session.revoked_at = None
        session = existing_session
    access_token = create_access_token(user_id=user.id, session_id=session.id, role=user.role, settings=settings)
    return SessionTokens(access_token=access_token, refresh_token=raw_refresh_token)


def register_user(
    db: Session,
    *,
    full_name: str,
    email: str,
    password: str,
    user_agent: str | None,
    ip_address: str | None,
    settings: Settings,
) -> AuthResponse:
    existing = db.scalar(select(User).where(User.email == email.lower()))
    if existing:
        raise conflict("An account with this email already exists.", "email_already_registered")
    user = User(
        full_name=full_name,
        email=email.lower(),
        password_hash=hash_password(password),
        role="user",
        preferred_practice_areas=[],
        notification_preferences={
            "product_updates": True,
            "support_followups": True,
            "security_alerts": True,
        },
        created_at=now_utc(),
        updated_at=now_utc(),
    )
    db.add(user)
    db.flush()
    tokens = create_session(
        db,
        user=user,
        settings=settings,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    write_audit_log(
        db,
        actor_type="user",
        actor_id=user.id,
        action="auth.register",
        entity_type="user",
        entity_id=user.id,
        metadata={"email": user.email},
    )
    db.commit()
    db.refresh(user)
    return AuthResponse(user=build_auth_user(user), session=tokens)


def login_user(
    db: Session,
    *,
    email: str,
    password: str,
    user_agent: str | None,
    ip_address: str | None,
    settings: Settings,
) -> AuthResponse:
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None or not verify_password(password, user.password_hash):
        raise unauthorized("Invalid email or password.", "invalid_credentials")
    tokens = create_session(
        db,
        user=user,
        settings=settings,
        user_agent=user_agent,
        ip_address=ip_address,
    )
    write_audit_log(
        db,
        actor_type="user",
        actor_id=user.id,
        action="auth.login",
        entity_type="user_session",
        entity_id=user.id,
        metadata={},
    )
    db.commit()
    return AuthResponse(user=build_auth_user(user), session=tokens)


def refresh_user_session(db: Session, *, refresh_token: str, settings: Settings, user_agent: str | None, ip_address: str | None) -> AuthResponse:
    session = db.scalar(select(UserSession).where(UserSession.refresh_token_hash == hash_token(refresh_token)))
    if session is None or session.revoked_at is not None or session.expires_at < now_utc():
        raise unauthorized("Invalid refresh token.", "invalid_refresh_token")
    user = db.get(User, session.user_id)
    tokens = create_session(
        db,
        user=user,
        settings=settings,
        user_agent=user_agent,
        ip_address=ip_address,
        existing_session=session,
    )
    write_audit_log(
        db,
        actor_type="user",
        actor_id=user.id,
        action="auth.refresh",
        entity_type="user_session",
        entity_id=session.id,
        metadata={},
    )
    db.commit()
    return AuthResponse(user=build_auth_user(user), session=tokens)


def revoke_session(db: Session, *, session: UserSession, actor_id: str) -> None:
    session.revoked_at = now_utc()
    write_audit_log(
        db,
        actor_type="user",
        actor_id=actor_id,
        action="auth.logout",
        entity_type="user_session",
        entity_id=session.id,
        metadata={},
    )
    db.commit()


def build_session_response(user: User) -> SessionResponse:
    return SessionResponse(authenticated=True, user=build_auth_user(user))


def issue_password_reset_token(db: Session, *, user: User, settings: Settings) -> str:
    raw_token = generate_opaque_token("reset")
    db.add(
        PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=now_utc() + timedelta(minutes=settings.password_reset_ttl_minutes),
            created_at=now_utc(),
        )
    )
    write_audit_log(
        db,
        actor_type="user",
        actor_id=user.id,
        action="auth.password_reset_requested",
        entity_type="user",
        entity_id=user.id,
        metadata={"delivery": "email_provider_pending"},
    )
    db.commit()
    return raw_token


def reset_password(db: Session, *, token: str, new_password: str) -> None:
    token_row = db.scalar(
        select(PasswordResetToken).where(
            PasswordResetToken.token_hash == hash_token(token),
            PasswordResetToken.used_at.is_(None),
        )
    )
    if token_row is None or token_row.expires_at < now_utc():
        raise unauthorized("Invalid or expired reset token.", "invalid_reset_token")
    user = db.get(User, token_row.user_id)
    user.password_hash = hash_password(new_password)
    user.updated_at = now_utc()
    token_row.used_at = now_utc()
    for session in db.scalars(select(UserSession).where(UserSession.user_id == user.id, UserSession.revoked_at.is_(None))).all():
        session.revoked_at = now_utc()
    write_audit_log(
        db,
        actor_type="user",
        actor_id=user.id,
        action="auth.password_reset_completed",
        entity_type="user",
        entity_id=user.id,
        metadata={},
    )
    db.commit()


def issue_email_verification_token(db: Session, *, user: User, settings: Settings) -> str:
    raw_token = generate_opaque_token("verify")
    db.add(
        EmailVerificationToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=now_utc() + timedelta(hours=settings.email_verification_ttl_hours),
            created_at=now_utc(),
        )
    )
    db.commit()
    return raw_token


def verify_email(db: Session, *, token: str) -> None:
    token_row = db.scalar(
        select(EmailVerificationToken).where(
            EmailVerificationToken.token_hash == hash_token(token),
            EmailVerificationToken.used_at.is_(None),
        )
    )
    if token_row is None or token_row.expires_at < now_utc():
        raise unauthorized("Invalid or expired verification token.", "invalid_verification_token")
    user = db.get(User, token_row.user_id)
    user.email_verified_at = now_utc()
    user.updated_at = now_utc()
    token_row.used_at = now_utc()
    write_audit_log(
        db,
        actor_type="user",
        actor_id=user.id,
        action="auth.email_verified",
        entity_type="user",
        entity_id=user.id,
        metadata={},
    )
    db.commit()


def get_user_or_404(db: Session, user_id: str) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise not_found("User not found.", "user_not_found")
    return user
