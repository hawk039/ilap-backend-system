from datetime import UTC, datetime

from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models import SupportRequest
from app.services.audit import write_audit_log


def create_support_request(
    db: Session,
    *,
    kind: str,
    name: str,
    email: str,
    subject: str,
    message: str,
    source: str,
) -> SupportRequest:
    now = datetime.now(UTC)
    record = SupportRequest(
        type=kind,
        name=name,
        email=email.lower(),
        subject=subject,
        message=message,
        source=source,
        status="open",
        created_at=now,
        updated_at=now,
    )
    db.add(record)
    db.flush()
    write_audit_log(
        db,
        actor_type="guest",
        actor_id=None,
        action=f"support.{kind}_created",
        entity_type="support_request",
        entity_id=record.id,
        metadata={"source": source},
    )
    db.commit()
    db.refresh(record)
    return record


def list_support_requests(db: Session, *, kind: str, limit: int, offset: int) -> list[SupportRequest]:
    return list(
        db.scalars(
            select(SupportRequest)
            .where(SupportRequest.type == kind)
            .order_by(desc(SupportRequest.created_at))
            .offset(offset)
            .limit(limit)
        ).all()
    )
