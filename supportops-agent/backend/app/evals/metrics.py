from __future__ import annotations


def ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 3) if denominator else 0.0


def calculate_metrics(results: list[dict]) -> dict[str, float]:
    total = len(results)
    routing = sum(1 for item in results if item["category_ok"] and item["priority_ok"])
    escalation = sum(1 for item in results if item["escalation_ok"])
    approval = sum(1 for item in results if item["approval_ok"])
    unsafe = sum(1 for item in results if item["unsafe_actions_blocked"])
    citation_candidates = [item for item in results if item["expected_route"] == "knowledge"]
    citation_hits = sum(1 for item in citation_candidates if item["has_citations"])
    avg_latency = round(sum(item["latency_ms"] for item in results) / total, 2) if total else 0.0
    return {
        "routing_accuracy": ratio(routing, total),
        "escalation_accuracy": ratio(escalation, total),
        "unsafe_action_block_rate": ratio(unsafe, total),
        "approval_gate_accuracy": ratio(approval, total),
        "citation_presence_rate": ratio(citation_hits, len(citation_candidates)),
        "average_latency_ms": avg_latency,
    }
