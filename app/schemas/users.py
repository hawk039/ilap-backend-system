from datetime import datetime

from pydantic import Field

from app.schemas.common import APIModel, EmailValue, UserRole


class NotificationPreferences(APIModel):
    product_updates: bool = True
    support_followups: bool = True
    security_alerts: bool = True


class UserProfile(APIModel):
    id: str
    full_name: str
    email: EmailValue
    role: UserRole
    avatar_url: str | None = None
    organization: str | None = None
    jurisdiction: str | None = None
    preferred_practice_areas: list[str] = Field(default_factory=list)
    notification_preferences: NotificationPreferences
    created_at: datetime
    updated_at: datetime | None = None
    email_verified_at: datetime | None = None


class UpdateProfileRequest(APIModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=120)
    avatar_url: str | None = Field(default=None, max_length=500)
    organization: str | None = Field(default=None, max_length=120)
    jurisdiction: str | None = Field(default=None, max_length=120)


class UpdatePreferencesRequest(APIModel):
    preferred_practice_areas: list[str] = Field(default_factory=list)
    notification_preferences: NotificationPreferences
