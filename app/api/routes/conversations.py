from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user, get_request_id
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.schemas.conversations import (
    AskConversationRequest,
    AskConversationResponse,
    ConversationMessage,
    ConversationSummary,
    CreateConversationRequest,
    UpdateConversationRequest,
)
from app.services import conversations as conversation_service
from app.services.rate_limit import enforce_rate_limit

router = APIRouter()


@router.post("", response_model=ConversationSummary, status_code=status.HTTP_201_CREATED)
def create_conversation(
    payload: CreateConversationRequest,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationSummary:
    item = conversation_service.create_conversation(db, user=current.user, payload=payload)
    return conversation_service.to_summary(item)


@router.get("", response_model=list[ConversationSummary])
def list_user_conversations(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ConversationSummary]:
    return [conversation_service.to_summary(item) for item in conversation_service.list_conversations(db, user_id=current.user.id, limit=limit, offset=offset)]


@router.get("/{conversation_id}", response_model=ConversationSummary)
def get_conversation(
    conversation_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationSummary:
    item = conversation_service.get_conversation_for_user(db, user_id=current.user.id, conversation_id=conversation_id)
    return conversation_service.to_summary(item)


@router.patch("/{conversation_id}", response_model=ConversationSummary)
def update_conversation(
    conversation_id: str,
    payload: UpdateConversationRequest,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationSummary:
    item = conversation_service.get_conversation_for_user(db, user_id=current.user.id, conversation_id=conversation_id)
    updated = conversation_service.update_conversation(db, conversation=item, payload=payload, actor_id=current.user.id)
    return conversation_service.to_summary(updated)


@router.delete("/{conversation_id}", response_model=ConversationSummary)
def delete_conversation(
    conversation_id: str,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversationSummary:
    item = conversation_service.get_conversation_for_user(db, user_id=current.user.id, conversation_id=conversation_id)
    updated = conversation_service.update_conversation(
        db,
        conversation=item,
        payload=UpdateConversationRequest(status="deleted"),
        actor_id=current.user.id,
    )
    return conversation_service.to_summary(updated)


@router.get("/{conversation_id}/messages", response_model=list[ConversationMessage])
def list_messages(
    conversation_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ConversationMessage]:
    conversation_service.get_conversation_for_user(db, user_id=current.user.id, conversation_id=conversation_id)
    return conversation_service.get_messages(db, conversation_id=conversation_id, limit=limit, offset=offset)


@router.post("/{conversation_id}/messages", response_model=AskConversationResponse)
@router.post("/{conversation_id}/ask", response_model=AskConversationResponse)
async def ask_conversation(
    conversation_id: str,
    payload: AskConversationRequest,
    request: Request,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
    request_id: str = Depends(get_request_id),
) -> AskConversationResponse:
    enforce_rate_limit(
        key=f"ask:{current.user.id}:{request.client.host if request.client else 'unknown'}",
        limit=settings.ask_rate_limit_per_minute,
        window_seconds=60,
    )
    conversation = conversation_service.get_conversation_for_user(db, user_id=current.user.id, conversation_id=conversation_id)
    return await conversation_service.ask_conversation(
        db,
        conversation=conversation,
        user=current.user,
        query=payload.query,
        idempotency_key=payload.idempotency_key,
        settings=settings,
        request_id=request_id,
    )
