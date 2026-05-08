from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.security import hash_password
from app.models import LegalCategory, User

CATEGORY_SEED = [
    {
        "id": "criminal-law",
        "name": "Criminal Law",
        "law_type": "Criminal Law",
        "description": "Offences, bail, FIRs, arrests, and trial procedure.",
        "icon_key": "gavel",
        "sort_order": 1,
    },
    {
        "id": "cyber-law",
        "name": "Cyber Law",
        "law_type": "Cyber Law",
        "description": "Cybercrime, privacy, data misuse, and digital evidence issues.",
        "icon_key": "shield",
        "sort_order": 2,
    },
    {
        "id": "family-law",
        "name": "Family Law",
        "law_type": "Family Law",
        "description": "Marriage, divorce, maintenance, custody, and succession questions.",
        "icon_key": "users",
        "sort_order": 3,
    },
]


def seed_baseline_data(db: Session, settings: Settings) -> None:
    now = datetime.now(UTC)
    if settings.seed_reference_data:
        for item in CATEGORY_SEED:
            category = db.get(LegalCategory, item["id"])
            if category is None:
                db.add(
                    LegalCategory(
                        **item,
                        is_active=True,
                        created_at=now,
                        updated_at=now,
                    )
                )
    if settings.enable_admin_bootstrap:
        admin = db.scalar(select(User).where(User.email == settings.admin_bootstrap_email.lower()))
        if admin is None:
            db.add(
                User(
                    full_name="ILAP Admin",
                    email=settings.admin_bootstrap_email.lower(),
                    password_hash=hash_password(settings.admin_bootstrap_password),
                    role="admin",
                    preferred_practice_areas=[],
                    notification_preferences={
                        "product_updates": True,
                        "support_followups": True,
                        "security_alerts": True,
                    },
                    created_at=now,
                    updated_at=now,
                )
            )
    db.commit()
