# ILAP Backend System

FastAPI backend for the ILAP platform.

## Features

- Authentication and user management
- Legal category catalog
- Conversation and ask flows
- Support and admin routes
- SQLite by default, PostgreSQL-ready via environment variables

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

## Run

```bash
uvicorn app.main:app --reload
```

The healthcheck is available at `/`.

## Tests

```bash
pytest -q
```

## Notes for GitHub

- Local virtual environments are ignored
- Local database files are ignored
- `.env` files are ignored
- Use `.env.example` as the safe template for collaborators
