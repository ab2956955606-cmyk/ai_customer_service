from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.evals.runner import get_latest_results, run_evaluation

router = APIRouter(prefix="/api/evals", tags=["evals"])


@router.post("/run")
def run(db: Session = Depends(get_db)) -> dict:
    return run_evaluation(db)


@router.get("/latest")
def latest() -> dict:
    return get_latest_results()
