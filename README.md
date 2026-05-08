# ILAP Backend System

FastAPI backend for the ILAP platform.

## Features

- Authentication and user management
- Legal category catalog
- Conversation and ask flows
- Support and admin routes
- SQLite by default, PostgreSQL-ready via environment variables
- Render-ready deployment via `render.yaml`

## Requirements

- Python 3.11+

## Local setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
```

## Environment

Copy `.env.example` to `.env` and adjust values for your machine.

Key variables:

- `DATABASE_URL`
- `SYNC_DATABASE_URL`
- `JWT_SECRET_KEY`
- `ADMIN_BOOTSTRAP_EMAIL`
- `ADMIN_BOOTSTRAP_PASSWORD`
- `CORS_ORIGINS`
- `AI_SERVICE_BASE_URL`
- `RESEND_API_KEY`
- `AUTH_EMAIL_FROM`
- `EMAIL_VERIFICATION_URL_TEMPLATE`
- `PASSWORD_RESET_URL_TEMPLATE`
- `UPSTASH_REDIS_REST_URL`
- `UPSTASH_REDIS_REST_TOKEN`

## Run

```bash
uvicorn app.main:app --reload
```

Health checks are available at `/` and `/healthz`.

By default, the backend uses `AI_SERVICE_BASE_URL=https://ilap-backend.onrender.com`, so AI conversation requests are sent to `POST https://ilap-backend.onrender.com/ask`.

## Tests

```bash
pytest -q
```

## Notes for GitHub

- Local virtual environments are ignored
- Local database files are ignored
- `.env` files are ignored
- Use `.env.example` as the safe template for collaborators

## Render deployment

This repo includes a [`render.yaml`](/Users/mayankdhyani/projects/ilap_backend_system/render.yaml) blueprint for a Python web service plus Render Postgres.

Important production notes:

- Set `ENVIRONMENT=production`
- Use Render Postgres for both `DATABASE_URL` and `SYNC_DATABASE_URL`
- Keep `AUTO_CREATE_SCHEMA=false`
- Set `REQUIRE_VERIFIED_EMAIL=true`
- Configure Resend for password reset and verification email delivery
- Configure Upstash Redis for production-safe rate limiting
- The startup command runs `alembic upgrade head` before starting Uvicorn
- The service listens on `0.0.0.0:$PORT`

After deployment, use the service URL plus `/docs` to test the API from your app integration environment.
