from datetime import datetime

from pydantic import Field

from app.schemas.common import APIModel, EmailValue, SupportStatus, SupportType


class SupportRequestCreate(APIModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailValue
    subject: str = Field(min_length=2, max_length=200)
    message: str = Field(min_length=5, max_length=5000)
    source: str = Field(min_length=2, max_length=100)


class SupportRequestResponse(APIModel):
    id: str
    type: SupportType
    name: str
    email: EmailValue
    subject: str
    message: str
    source: str
    status: SupportStatus
    created_at: datetime
    updated_at: datetime | None = None
