"""FastAPI application entrypoint for Sentinel Lens."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.models.database import init_db
from app.api.sessions import router as sessions_router
from app.api.evaluations import router as evaluations_router
from app.api.auth import router as auth_router
from app.api.system import router as system_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Enforce production safety: demo mode strictly prohibited in production
    settings.check_production_safety()
    # Initialize SQLite tables
    init_db()
    yield


def create_app() -> FastAPI:
    """Factory function creating the configured Sentinel Lens FastAPI application."""
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Next generation e2e testing framework with programmatic runner embedding and AI agent test execution.",
        lifespan=lifespan,
    )

    # CORS configuration for local React Vite frontend
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routers
    application.include_router(sessions_router, prefix="/api/v1")
    application.include_router(evaluations_router, prefix="/api/v1")
    application.include_router(auth_router, prefix="/api/v1")
    application.include_router(system_router, prefix="/api/v1")

    @application.get("/", response_class=JSONResponse)
    def root():
        return {
            "app": settings.app_name,
            "version": settings.app_version,
            "status": "online",
            "docs_url": "/docs",
            "runner_endpoint": "/api/v1/sessions",
        }

    return application


# Global application instance exported for uvicorn entrypoint
app = create_app()
