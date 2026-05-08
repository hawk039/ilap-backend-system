from datetime import datetime
from typing import Any

from pydantic import Field

from app.schemas.common import APIModel, EmailValue, SupportStatus, UserRole


class AdminUserSummary(APIModel):
    id: str
    full_name: str
    email: EmailValue
    role: UserRole
    created_at: datetime
    email_verified_at: datetime | None = None


class AdminConversationSummary(APIModel):
    id: str
    user_id: str
    title: str
    law_type: str
    status: str
    last_message_at: datetime | None = None
    updated_at: datetime | None = None


class AdminSupportSummary(APIModel):
    id: str
    type: str
    name: str
    email: EmailValue
    status: SupportStatus
    created_at: datetime


class AuditLogResponse(APIModel):
    id: str
    actor_type: str
    actor_id: str | None = None
    action: str
    entity_type: str
    entity_id: str
    metadata: dict[str, Any] = Field(validation_alias="metadata_json")
    created_at: datetime
