# Backend Architecture

## Overview

The ILAP backend is a FastAPI application organized by API routes, services, schemas, models, and database helpers.

## Main components

- `app/main.py`: application factory, middleware, exception handlers, and lifespan setup
- `app/api/routes/`: HTTP endpoints grouped by domain
- `app/services/`: business logic and bootstrap helpers
- `app/models/`: SQLAlchemy ORM entities
- `app/schemas/`: request and response models
- `app/db/`: engine, session, and metadata wiring
- `migrations/`: Alembic migration files

## Configuration

Runtime settings are loaded from environment variables in `app/core/config.py`.

Important operational settings:

- Database connection URLs
- JWT secret and token TTLs
- CORS origins
- AI integration base URL and stub mode
- Admin bootstrap credentials

## Startup behavior

On startup, the app can automatically create the schema and seed baseline data when `AUTO_CREATE_SCHEMA=true`.

## Testing

The test suite uses temporary SQLite databases and clears cached settings before app creation.
