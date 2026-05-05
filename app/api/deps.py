from dataclasses import dataclass

from fastapi import Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.errors import forbidden, unauthorized
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User, UserSession


@dataclass
class CurrentUser:
    user: User
    session: UserSession


def get_request_id(request: Request) -> str:
    return request.state.request_id


def get_current_user(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CurrentUser:
    if not authorization.startswith("Bearer "):
        raise unauthorized()
    payload = decode_access_token(authorization.split(" ", 1)[1], settings)
    session = db.scalar(select(UserSession).where(UserSession.id == payload["sid"]))
    if session is None or session.revoked_at is not None:
        raise unauthorized()
    user = db.scalar(select(User).where(User.id == payload["sub"]))
    if user is None:
        raise unauthorized()
    return CurrentUser(user=user, session=session)


def require_admin(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current.user.role != "admin":
        raise forbidden("Admin privileges are required.")
    return current
