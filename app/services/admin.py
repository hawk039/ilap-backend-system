from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import AuditLog, Conversation, SupportRequest, User


def list_users(db: Session, *, limit: int, offset: int) -> list[User]:
    return list(db.scalars(select(User).order_by(desc(User.created_at)).offset(offset).limit(limit)).all())


def list_conversations(db: Session, *, limit: int, offset: int) -> list[Conversation]:
    return list(db.scalars(select(Conversation).order_by(desc(Conversation.updated_at)).offset(offset).limit(limit)).all())


def list_support(db: Session, *, kind: str, limit: int, offset: int) -> list[SupportRequest]:
    return list(
        db.scalars(
            select(SupportRequest)
            .where(SupportRequest.type == kind)
            .order_by(desc(SupportRequest.created_at))
            .offset(offset)
            .limit(limit)
        ).all()
    )


def list_audit_logs(db: Session, *, limit: int, offset: int) -> list[AuditLog]:
    return list(db.scalars(select(AuditLog).order_by(desc(AuditLog.created_at)).offset(offset).limit(limit)).all())
