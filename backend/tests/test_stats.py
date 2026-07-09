from __future__ import annotations


def test_stats_endpoint_returns_overview(client):
    client.post(
        "/api/tickets",
        json={
            "subject": "Cannot reset password",
            "description": "The reset link is not arriving.",
            "customer_email": "alice@example.com",
        },
    )
    response = client.get("/api/stats/overview")
    assert response.status_code == 200
    body = response.json()
    assert body["total_tickets"] >= 1
    assert "category_breakdown" in body
    assert "recent_runs" in body
