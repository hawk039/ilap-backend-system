from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.db.session import get_db
from app.schemas.admin import AdminConversationSummary, AdminSupportSummary, AdminUserSummary, AuditLogResponse
from app.services import admin as admin_service

router = APIRouter()


@router.get("/users", response_model=list[AdminUserSummary])
def list_users(
    _: object = Depends(require_admin),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[AdminUserSummary]:
    return [AdminUserSummary.model_validate(item) for item in admin_service.list_users(db, limit=limit, offset=offset)]


@router.get("/conversations", response_model=list[AdminConversationSummary])
def list_conversations(
    _: object = Depends(require_admin),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[AdminConversationSummary]:
    return [AdminConversationSummary.model_validate(item) for item in admin_service.list_conversations(db, limit=limit, offset=offset)]


@router.get("/support-tickets", response_model=list[AdminSupportSummary])
def list_support_tickets(
    _: object = Depends(require_admin),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[AdminSupportSummary]:
    return [AdminSupportSummary.model_validate(item) for item in admin_service.list_support(db, kind="support", limit=limit, offset=offset)]


@router.get("/contact-requests", response_model=list[AdminSupportSummary])
def list_contact_requests(
    _: object = Depends(require_admin),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[AdminSupportSummary]:
    return [AdminSupportSummary.model_validate(item) for item in admin_service.list_support(db, kind="contact", limit=limit, offset=offset)]


@router.get("/audit-logs", response_model=list[AuditLogResponse])
def list_audit_logs(
    _: object = Depends(require_admin),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[AuditLogResponse]:
    return [AuditLogResponse.model_validate(item) for item in admin_service.list_audit_logs(db, limit=limit, offset=offset)]
