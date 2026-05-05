from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.support import SupportRequestCreate, SupportRequestResponse
from app.services.support import create_support_request

router = APIRouter()


@router.post("/contact-requests", response_model=SupportRequestResponse, status_code=status.HTTP_201_CREATED)
def create_contact_request(payload: SupportRequestCreate, db: Session = Depends(get_db)) -> SupportRequestResponse:
    record = create_support_request(
        db,
        kind="contact",
        name=payload.name,
        email=payload.email,
        subject=payload.subject,
        message=payload.message,
        source=payload.source,
    )
    return SupportRequestResponse.model_validate(record)


@router.post("/support-tickets", response_model=SupportRequestResponse, status_code=status.HTTP_201_CREATED)
def create_support_ticket(payload: SupportRequestCreate, db: Session = Depends(get_db)) -> SupportRequestResponse:
    record = create_support_request(
        db,
        kind="support",
        name=payload.name,
        email=payload.email,
        subject=payload.subject,
        message=payload.message,
        source=payload.source,
    )
    return SupportRequestResponse.model_validate(record)


@router.post("/early-access-requests", response_model=SupportRequestResponse, status_code=status.HTTP_201_CREATED)
def create_early_access_request(payload: SupportRequestCreate, db: Session = Depends(get_db)) -> SupportRequestResponse:
    record = create_support_request(
        db,
        kind="early_access",
        name=payload.name,
        email=payload.email,
        subject=payload.subject,
        message=payload.message,
        source=payload.source,
    )
    return SupportRequestResponse.model_validate(record)
