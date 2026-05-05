from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, StringConstraints


def to_camel(value: str) -> str:
    first, *rest = value.split("_")
    return first + "".join(piece.capitalize() for piece in rest)


class APIModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, alias_generator=to_camel, from_attributes=True)


EmailValue = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=5,
        max_length=320,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
    ),
]

ConversationStatus = Literal["active", "archived", "deleted"]
SupportStatus = Literal["open", "in_review", "resolved"]
SupportType = Literal["contact", "support", "early_access"]
UserRole = Literal["user", "admin"]


class MessageResponse(APIModel):
    message: str


class ErrorMessage(APIModel):
    code: str
    message: str


class ErrorResponse(APIModel):
    error: ErrorMessage
    request_id: str | None = None


class Timestamped(APIModel):
    created_at: datetime
    updated_at: datetime | None = None
