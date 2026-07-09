from __future__ import annotations


def test_rag_returns_citations(client):
    response = client.post("/api/rag/ask", json={"question": "How can I cancel my subscription?"})
    assert response.status_code == 200
    body = response.json()
    assert body["citations"]
    assert any(citation["title"] == "subscription_cancellation.md" for citation in body["citations"])
