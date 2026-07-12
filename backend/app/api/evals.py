from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy.orm import Session

from app.agents.llm import DeepSeekLLMClient, temporary_llm_client
from app.db import get_db
from app.evals.runner import EvalLocale, get_latest_results, run_evaluation

router = APIRouter(prefix="/api/evals", tags=["evals"])


@router.post("/run")
def run(
    db: Session = Depends(get_db),
    locale: Annotated[EvalLocale, Query()] = "en",
    deepseek_api_key: Annotated[
        str | None,
        Header(alias="X-DeepSeek-API-Key", max_length=512),
    ] = None,
) -> dict:
    if deepseek_api_key:
        client = DeepSeekLLMClient(deepseek_api_key)
        with temporary_llm_client(client):
            return run_evaluation(db, llm_client=client, locale=locale)
    return run_evaluation(db, locale=locale)


@router.get("/latest")
def latest(locale: Annotated[EvalLocale, Query()] = "en") -> dict:
    return get_latest_results(locale)
