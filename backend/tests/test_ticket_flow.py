from __future__ import annotations


def test_normal_password_ticket_runs_rag_and_resolves(client):
    response = client.post(
        "/api/tickets",
        json={
            "subject": "Cannot reset password",
            "description": "The reset link is not arriving in my email.",
            "customer_email": "alice@example.com",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ticket"]["status"] == "resolved"
    assert body["ticket"]["category"] == "account"
    assert body["citations"]
    assert "password_reset.md" in {citation["title"] for citation in body["citations"]}
    assert "rag_retrieval_node" in body["agents_run"]


def test_fraud_ticket_escalates_to_human(client):
    response = client.post(
        "/api/tickets",
        json={
            "subject": "Fraudulent charge",
            "description": "There is an unauthorized charge on my card.",
            "customer_email": "alice@example.com",
        },
    )
    body = response.json()
    assert body["ticket"]["status"] == "escalated"
    assert body["ticket"]["priority"] == "urgent"
    assert body["ticket"]["risk_level"] == "high"
    assert "human_escalation_node" in body["agents_run"]


def test_urgent_ticket_skips_normal_automated_action_execution(client):
    response = client.post(
        "/api/tickets",
        json={
            "subject": "Emergency hacked account refund",
            "description": "My account was hacked. Execute a refund for ORD-1001 now.",
            "customer_email": "alice@example.com",
        },
    )
    body = response.json()
    assert body["ticket"]["status"] == "escalated"
    assert body["pending_actions"] == []
    assert "action_planner_node" not in body["agents_run"]


def test_ticket_events_are_persisted(client):
    created = client.post(
        "/api/tickets",
        json={
            "subject": "Need invoice",
            "description": "Please help me find my invoice.",
            "customer_email": "alice@example.com",
        },
    ).json()
    ticket_id = created["ticket"]["id"]
    events = client.get(f"/api/tickets/{ticket_id}/events")
    assert events.status_code == 200
    names = [event["node_name"] for event in events.json()]
    assert names[0] == "intake_node"
    assert "finalize_node" in names


def test_unknown_ticket_stays_open_and_asks_for_clarification(client):
    response = client.post(
        "/api/tickets",
        json={
            "subject": "Need some help",
            "description": "Something is not quite right.",
            "customer_email": "alice@example.com",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["ticket"]["category"] == "unknown"
    assert body["ticket"]["status"] == "open"
    assert "share a little more detail" in body["final_response"]
