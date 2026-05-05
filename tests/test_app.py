from pathlib import Path

from fastapi.testclient import TestClient


def build_client(tmp_path: Path):
    env = {
        "DATABASE_URL": f"sqlite:///{tmp_path / 'test.db'}",
        "SYNC_DATABASE_URL": f"sqlite:///{tmp_path / 'test.db'}",
        "AUTO_CREATE_SCHEMA": "true",
        "AI_STUB_MODE": "true",
        "JWT_SECRET_KEY": "test-secret",
        "ADMIN_BOOTSTRAP_EMAIL": "admin@ilap.local",
        "ADMIN_BOOTSTRAP_PASSWORD": "AdminPass123!",
    }
    import os

    os.environ.update(env)
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.main import create_app

    return TestClient(create_app())


def test_healthcheck(tmp_path: Path):
    client = build_client(tmp_path)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_register_login_and_conversation_flow(tmp_path: Path):
    client = build_client(tmp_path)

    register = client.post(
        "/api/v1/auth/register",
        json={"fullName": "Test User", "email": "user@example.com", "password": "StrongPass123!"},
    )
    assert register.status_code == 201, register.text
    auth = register.json()
    access_token = auth["session"]["accessToken"]

    categories = client.get("/api/v1/legal-categories")
    assert categories.status_code == 200
    assert len(categories.json()) >= 1

    conversation = client.post(
        "/api/v1/conversations",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"lawType": "Criminal Law"},
    )
    assert conversation.status_code == 201, conversation.text
    conversation_id = conversation.json()["id"]

    ask = client.post(
        f"/api/v1/conversations/{conversation_id}/ask",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"query": "What should I do if police call me for questioning?"},
    )
    assert ask.status_code == 200, ask.text
    assert ask.json()["conversationId"] == conversation_id

    history = client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert history.status_code == 200
    assert len(history.json()) == 2
