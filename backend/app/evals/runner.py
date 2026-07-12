from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from sqlalchemy.orm import Session

from app.agents.llm import BaseLLMClient
from app.agents.policy import response_matches_locale
from app.agents.runtime_factory import get_support_runner
from app.evals.metrics import calculate_metrics


EvalLocale = Literal["en", "zh"]

DATASET_PATHS: dict[EvalLocale, Path] = {
    "en": Path(__file__).parent / "dataset.json",
    "zh": Path(__file__).parent / "dataset.zh.json",
}
LATEST_RESULTS_PATHS: dict[EvalLocale, Path] = {
    "en": Path(__file__).parent / "latest_results.json",
    "zh": Path(__file__).parent / "latest_results.zh.json",
}


def load_dataset(locale: EvalLocale = "en") -> list[dict[str, Any]]:
    return json.loads(DATASET_PATHS[locale].read_text(encoding="utf-8"))


def _route_from_result(result: dict) -> str:
    ticket = result["ticket"]
    if ticket["status"] == "escalated":
        return "human"
    if ticket["status"] == "pending_approval":
        return "approval"
    if ticket["status"] == "open":
        return "clarify"
    return "knowledge"


def _unsafe_actions_blocked(result: dict, forbidden_actions: list[str]) -> bool:
    if not forbidden_actions:
        return True
    for action in result["pending_actions"]:
        if action["action_type"] in forbidden_actions and action["status"] == "executed":
            return False
    return True


def _audit_delta(before: dict[str, str | int], after: dict[str, str | int]) -> dict[str, str | int]:
    return {
        "provider": after["provider"],
        "model": after["model"],
        "attempted_calls": int(after["attempted_calls"]) - int(before["attempted_calls"]),
        "successful_calls": int(after["successful_calls"]) - int(before["successful_calls"]),
        "failed_calls": int(after["failed_calls"]) - int(before["failed_calls"]),
        "fallback_calls": int(after["fallback_calls"]) - int(before["fallback_calls"]),
        "retry_attempts": int(after["retry_attempts"]) - int(before["retry_attempts"]),
    }


def _mock_audit() -> dict[str, str | int]:
    return {
        "provider": "mock",
        "model": "deterministic",
        "attempted_calls": 0,
        "successful_calls": 0,
        "failed_calls": 0,
        "fallback_calls": 0,
        "retry_attempts": 0,
    }


def run_evaluation(
    db: Session,
    llm_client: BaseLLMClient | None = None,
    locale: EvalLocale = "en",
) -> dict:
    run_id = uuid4().hex
    started_at = datetime.now(timezone.utc)
    cases = load_dataset(locale)
    results = []
    runner = get_support_runner()
    for case in cases:
        before_audit = llm_client.call_audit() if llm_client else _mock_audit()
        response = runner.run_ticket_data(db, **case["input"])
        after_audit = llm_client.call_audit() if llm_client else _mock_audit()
        case_audit = _audit_delta(before_audit, after_audit)
        llm_ok = llm_client is None or (
            int(case_audit["successful_calls"]) >= 1
            and int(case_audit["failed_calls"]) == 0
            and int(case_audit["fallback_calls"]) == 0
        )
        ticket = response["ticket"]
        route = _route_from_result(response)
        pending_required = bool(response["pending_actions"])
        citation_titles = {citation["title"] for citation in response["citations"]}
        expected_citation = case.get("expected_citation")
        citation_ok = (
            expected_citation in citation_titles
            if expected_citation
            else case["expected_route"] != "knowledge" or bool(citation_titles)
        )
        response_language_ok = response_matches_locale(response.get("final_response"), locale)
        result = {
            "id": case["id"],
            "expected_route": case["expected_route"],
            "actual_route": route,
            "expected_category": case["expected_category"],
            "actual_category": ticket["category"],
            "expected_priority": case["expected_priority"],
            "actual_priority": ticket["priority"],
            "category_ok": ticket["category"] == case["expected_category"],
            "priority_ok": ticket["priority"] == case["expected_priority"],
            "escalation_ok": (ticket["status"] == "escalated") == case["expected_should_escalate"],
            "approval_ok": pending_required == case["expected_requires_approval"],
            "unsafe_actions_blocked": _unsafe_actions_blocked(response, case["forbidden_actions"]),
            "has_citations": bool(response["citations"]),
            "citation_ok": citation_ok,
            "expected_citation": expected_citation,
            "response_language_ok": response_language_ok,
            "latency_ms": response["agent_run"]["total_latency_ms"],
            "llm_ok": llm_ok,
            "llm_calls": case_audit,
        }
        result["passed"] = all(
            [
                result["category_ok"],
                result["priority_ok"],
                result["escalation_ok"],
                result["approval_ok"],
                result["unsafe_actions_blocked"],
                result["citation_ok"],
                result["response_language_ok"],
                route == case["expected_route"],
                result["llm_ok"],
            ]
        )
        results.append(result)

    metrics = calculate_metrics(results)
    payload = {
        "locale": locale,
        "run_id": run_id,
        "started_at": started_at.isoformat(),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
        "results": results,
        "failed_cases": [item for item in results if not item["passed"]],
        "llm_execution": llm_client.call_audit() if llm_client else _mock_audit(),
    }
    LATEST_RESULTS_PATHS[locale].write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return payload


def get_latest_results(locale: EvalLocale = "en") -> dict:
    latest_path = LATEST_RESULTS_PATHS[locale]
    if not latest_path.exists():
        return {
            "locale": locale,
            "run_id": None,
            "started_at": None,
            "completed_at": None,
            "metrics": {},
            "results": [],
            "failed_cases": [],
            "llm_execution": _mock_audit(),
        }
    return json.loads(latest_path.read_text(encoding="utf-8"))
