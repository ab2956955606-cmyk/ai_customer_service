from __future__ import annotations


def test_eval_runner_returns_metrics(client):
    response = client.post("/api/evals/run")
    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["routing_accuracy"] >= 0.8
    assert body["metrics"]["unsafe_action_block_rate"] == 1
    assert len(body["results"]) >= 20


def test_latest_eval_returns_last_run(client):
    client.post("/api/evals/run")
    latest = client.get("/api/evals/latest")
    assert latest.status_code == 200
    assert latest.json()["metrics"]
