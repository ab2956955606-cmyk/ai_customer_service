from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from app.agents import langgraph_nodes as nodes
from app.agents.langgraph_state import SupportAgentState


def _route_after_risk_policy(state: SupportAgentState) -> str:
    if state.get("requires_human") or state.get("detected_injection") or state.get("risk_level") == "high":
        return "human_escalation"
    return "standard"


def _route_after_approval_gate(state: SupportAgentState) -> str:
    if any(action.get("status") == "pending" for action in state.get("pending_actions", [])):
        return "needs_approval"
    return "no_approval"


def build_support_graph():
    workflow = StateGraph(SupportAgentState)
    workflow.add_node("intake", nodes.intake)
    workflow.add_node("injection_guard", nodes.injection_guard)
    workflow.add_node("triage", nodes.triage)
    workflow.add_node("risk_policy", nodes.risk_policy)
    workflow.add_node("customer_lookup", nodes.customer_lookup)
    workflow.add_node("order_lookup", nodes.order_lookup)
    workflow.add_node("rag_retrieval", nodes.rag_retrieval)
    workflow.add_node("response_drafter", nodes.response_drafter)
    workflow.add_node("action_planner", nodes.action_planner)
    workflow.add_node("approval_gate", nodes.approval_gate)
    workflow.add_node("human_escalation", nodes.human_escalation)
    workflow.add_node("finalize", nodes.finalize)

    workflow.add_edge(START, "intake")
    workflow.add_edge("intake", "injection_guard")
    workflow.add_edge("injection_guard", "triage")
    workflow.add_edge("triage", "risk_policy")
    workflow.add_conditional_edges(
        "risk_policy",
        _route_after_risk_policy,
        {
            "human_escalation": "human_escalation",
            "standard": "customer_lookup",
        },
    )
    workflow.add_edge("customer_lookup", "order_lookup")
    workflow.add_edge("order_lookup", "rag_retrieval")
    workflow.add_edge("rag_retrieval", "response_drafter")
    workflow.add_edge("response_drafter", "action_planner")
    workflow.add_edge("action_planner", "approval_gate")
    workflow.add_conditional_edges(
        "approval_gate",
        _route_after_approval_gate,
        {
            "needs_approval": "finalize",
            "no_approval": "finalize",
        },
    )
    workflow.add_edge("human_escalation", "finalize")
    workflow.add_edge("finalize", END)
    return workflow.compile()
