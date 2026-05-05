from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, get_current_user
from app.db.session import get_db
from app.schemas.users import UpdatePreferencesRequest, UpdateProfileRequest, UserProfile
from app.services.auth import build_profile

router = APIRouter()


@router.get("/me", response_model=UserProfile)
def get_me(current: CurrentUser = Depends(get_current_user)) -> UserProfile:
    return build_profile(current.user)


@router.patch("/me", response_model=UserProfile)
def update_me(
    payload: UpdateProfileRequest,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    updates = payload.model_dump(exclude_none=True)
    for key, value in updates.items():
        setattr(current.user, key, value)
    current.user.updated_at = __import__("datetime").datetime.now(__import__("datetime").UTC)
    db.commit()
    db.refresh(current.user)
    return build_profile(current.user)


@router.patch("/me/preferences", response_model=UserProfile)
def update_preferences(
    payload: UpdatePreferencesRequest,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserProfile:
    current.user.preferred_practice_areas = payload.preferred_practice_areas
    current.user.notification_preferences = payload.notification_preferences.model_dump(mode="json")
    current.user.updated_at = __import__("datetime").datetime.now(__import__("datetime").UTC)
    db.commit()
    db.refresh(current.user)
    return build_profile(current.user)
