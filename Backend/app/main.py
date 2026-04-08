from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.core.config import get_settings
from app.database import engine
from app.api.v1 import (
    auth, students, recruiters, placement_officers, colleges,
    jobs, applications, rounds, offers, notifications,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Phase 1 — Auth & Profiles
    app.include_router(auth.router,                  prefix="/api/v1/auth",                tags=["Auth"])
    app.include_router(colleges.router,              prefix="/api/v1/colleges",            tags=["Colleges"])
    app.include_router(students.router,              prefix="/api/v1/students",            tags=["Students"])
    app.include_router(recruiters.router,            prefix="/api/v1/recruiters",          tags=["Recruiters"])
    app.include_router(placement_officers.router,    prefix="/api/v1/placement_officers",  tags=["Placement Officers"])

    # Phase 2 — Jobs & Applications
    app.include_router(jobs.router,          prefix="/api/v1/jobs",          tags=["Jobs"])
    app.include_router(applications.router,  prefix="/api/v1/applications",  tags=["Applications"])

    # Phase 3 — Rounds, Offers, Notifications
    app.include_router(rounds.router,         prefix="/api/v1",              tags=["Rounds"])
    app.include_router(offers.router,         prefix="/api/v1/offers",       tags=["Offers"])
    app.include_router(notifications.router,  prefix="/api/v1/notifications",tags=["Notifications"])

    @app.get("/health")
    async def health_check():
        return {"status": "ok", "app": settings.APP_NAME, "version": settings.APP_VERSION}

    return app


app = create_app()
