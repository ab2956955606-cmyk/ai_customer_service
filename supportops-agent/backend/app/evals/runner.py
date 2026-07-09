from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.agents.graph import run_ticket_workflow
from app.evals.metrics import calculate_metrics


DATASET_PATH = Path(__file__).parent / "dataset.json"
LATEST_RESULTS_PATH = Path(__file__).parent / "latest_results.json"


def load_dataset() -> list[dict[str, Any]]:
    return json.loads(DATASET_PATH.read_text(encoding="utf-8"))


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


def run_evaluation(db: Session) -> dict:
    cases = load_dataset()
    results = []
    for case in cases:
        response = run_ticket_workflow(db, **case["input"])
        ticket = response["ticket"]
        route = _route_from_result(response)
        pending_required = bool(response["pending_actions"])
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
            "latency_ms": response["agent_run"]["total_latency_ms"],
        }
        result["passed"] = all(
            [
                result["category_ok"],
                result["priority_ok"],
                result["escalation_ok"],
                result["approval_ok"],
                result["unsafe_actions_blocked"],
                route == case["expected_route"],
            ]
        )
        results.append(result)

    metrics = calculate_metrics(results)
    payload = {
        "metrics": metrics,
        "results": results,
        "failed_cases": [item for item in results if not item["passed"]],
    }
    LATEST_RESULTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


def get_latest_results() -> dict:
    if not LATEST_RESULTS_PATH.exists():
        return {"metrics": {}, "results": [], "failed_cases": []}
    return json.loads(LATEST_RESULTS_PATH.read_text(encoding="utf-8"))
