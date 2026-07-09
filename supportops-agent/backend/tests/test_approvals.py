from __future__ import annotations


def _create_refund_ticket(client) -> dict:
    return client.post(
        "/api/tickets",
        json={
            "subject": "Refund request for ORD-1001",
            "description": "I want a refund for order ORD-1001 because I bought the wrong item.",
            "customer_email": "alice@example.com",
        },
    ).json()


def test_refund_ticket_creates_pending_approval(client):
    body = _create_refund_ticket(client)
    assert body["ticket"]["status"] == "pending_approval"
    assert len(body["pending_actions"]) == 1
    action = body["pending_actions"][0]
    assert action["action_type"] == "create_refund_request"
    assert action["status"] == "pending"


def test_address_change_creates_pending_approval(client):
    body = client.post(
        "/api/tickets",
        json={
            "subject": "Change shipping address",
            "description": "Please update address for ORD-1001 to 88 New Street, Denver, CO.",
            "customer_email": "alice@example.com",
        },
    ).json()
    action = body["pending_actions"][0]
    assert body["ticket"]["status"] == "pending_approval"
    assert action["action_type"] == "update_shipping_address"
    assert action["payload_json"]["order_id"] is not None


def test_approval_endpoint_executes_pending_action(client):
    body = _create_refund_ticket(client)
    action_id = body["pending_actions"][0]["id"]
    approved = client.post(f"/api/approvals/{action_id}/approve")
    assert approved.status_code == 200
    payload = approved.json()
    assert payload["action"]["status"] == "executed"
    assert payload["ticket"]["status"] == "resolved"


def test_rejection_endpoint_rejects_pending_action(client):
    body = _create_refund_ticket(client)
    action_id = body["pending_actions"][0]["id"]
    rejected = client.post(f"/api/approvals/{action_id}/reject")
    assert rejected.status_code == 200
    payload = rejected.json()
    assert payload["action"]["status"] == "rejected"
    assert payload["ticket"]["status"] == "resolved"
