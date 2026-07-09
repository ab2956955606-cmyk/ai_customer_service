from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import approvals, evals, health, rag, stats, tickets
from app.config import get_settings
from app.db import SessionLocal, init_db
from app.seed import seed_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    del app
    init_db()
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(tickets.router)
    app.include_router(rag.router)
    app.include_router(approvals.router)
    app.include_router(stats.router)
    app.include_router(evals.router)
    return app


app = create_app()
