from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.core.config import Settings
from app.core.errors import unauthorized

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(*, user_id: str, session_id: str, role: str, settings: Settings) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": user_id,
        "sid": session_id,
        "role": role,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_ttl_minutes)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: Settings) -> dict:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.InvalidTokenError as exc:
        raise unauthorized("Invalid access token.", "invalid_access_token") from exc
    if payload.get("type") != "access":
        raise unauthorized("Invalid access token.", "invalid_access_token")
    return payload
