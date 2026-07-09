from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import KnowledgeDocument

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    db_status = "ok"
    try:
        db.execute(text("select 1"))
    except Exception:
        db_status = "error"
    retriever_status = "ready" if db.query(KnowledgeDocument).count() > 0 else "empty"
    settings = get_settings()
    return {
        "status": "ok" if db_status == "ok" else "degraded",
        "db": db_status,
        "llm_provider": settings.llm_provider,
        "retriever": retriever_status,
        "app": settings.app_name,
    }
