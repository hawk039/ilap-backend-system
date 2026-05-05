from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import APIError
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.services.bootstrap import seed_baseline_data


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    if settings.auto_create_schema:
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            seed_baseline_data(db, settings)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_context(request: Request, call_next):
        request.state.request_id = request.headers.get("X-Request-Id") or f"req_{uuid4().hex}"
        response = await call_next(request)
        response.headers["X-Request-Id"] = request.state.request_id
        return response

    @app.exception_handler(APIError)
    async def api_error_handler(request: Request, exc: APIError):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {"code": exc.code, "message": exc.message},
                "requestId": getattr(request.state, "request_id", None),
            },
        )

    @app.exception_handler(Exception)
    async def generic_error_handler(request: Request, _: Exception):
        return JSONResponse(
            status_code=500,
            content={
                "error": {"code": "internal_error", "message": "An unexpected error occurred."},
                "requestId": getattr(request.state, "request_id", None),
            },
        )

    @app.get("/", tags=["system"])
    async def healthcheck():
        return {
            "service": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
            "status": "ok",
        }

    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
