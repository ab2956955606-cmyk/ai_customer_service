from __future__ import annotations

import json

from app.agents.llm import DeepSeekLLMClient
from app.evals.runner import LATEST_RESULTS_PATHS


def test_eval_runner_returns_metrics(client):
    response = client.post("/api/evals/run")
    assert response.status_code == 200
    body = response.json()
    assert body["metrics"]["routing_accuracy"] == 1
    assert body["metrics"]["escalation_accuracy"] == 1
    assert body["metrics"]["unsafe_action_block_rate"] == 1
    assert body["metrics"]["approval_gate_accuracy"] == 1
    assert body["metrics"]["citation_presence_rate"] == 1
    assert body["metrics"]["response_language_accuracy"] == 1
    assert body["locale"] == "en"
    assert len(body["results"]) == 20
    assert body["failed_cases"] == []
    assert body["llm_execution"]["provider"] == "mock"


def test_latest_eval_returns_last_run(client):
    client.post("/api/evals/run")
    latest = client.get("/api/evals/latest")
    assert latest.status_code == 200
    assert latest.json()["metrics"]


def test_chinese_eval_is_isolated_and_passes_all_cases(client):
    english = client.post("/api/evals/run").json()
    chinese_response = client.post("/api/evals/run?locale=zh")

    assert chinese_response.status_code == 200
    chinese = chinese_response.json()
    assert chinese["locale"] == "zh"
    assert len(chinese["results"]) == 20
    assert chinese["failed_cases"] == []
    assert all(result["passed"] for result in chinese["results"])
    assert all(result["response_language_ok"] for result in chinese["results"])
    assert chinese["metrics"]["routing_accuracy"] == 1
    assert chinese["metrics"]["escalation_accuracy"] == 1
    assert chinese["metrics"]["unsafe_action_block_rate"] == 1
    assert chinese["metrics"]["approval_gate_accuracy"] == 1
    assert chinese["metrics"]["citation_presence_rate"] == 1
    assert chinese["metrics"]["response_language_accuracy"] == 1

    assert client.get("/api/evals/latest?locale=en").json()["run_id"] == english["run_id"]
    assert client.get("/api/evals/latest?locale=zh").json()["run_id"] == chinese["run_id"]


def test_eval_rejects_unsupported_locale(client):
    response = client.post("/api/evals/run?locale=fr")
    assert response.status_code == 422


def test_real_eval_audit_is_request_scoped(client, monkeypatch):
    def fake_request(self: DeepSeekLLMClient, body: dict) -> str:
        del self
        prompt = body["messages"][0]["content"]
        if "Return JSON" in prompt:
            return json.dumps(
                {
                    "category": "Model suggestion",
                    "priority": "High",
                    "risk_level": "Medium",
                    "requires_human": True,
                    "requires_approval": True,
                    "confidence": 0.99,
                }
            )
        return "DeepSeek drafted a response grounded in the supplied policy titles."

    monkeypatch.setattr(DeepSeekLLMClient, "_request_once", fake_request)
    api_key = "sk-eval-request-scope-test"

    response = client.post(
        "/api/evals/run",
        headers={"X-DeepSeek-API-Key": api_key},
    )

    assert response.status_code == 200
    assert api_key not in response.text
    body = response.json()
    assert len(body["results"]) == 20
    assert body["failed_cases"] == []
    assert all(result["passed"] for result in body["results"])
    assert all(result["llm_ok"] for result in body["results"])
    assert all(result["llm_calls"]["successful_calls"] >= 1 for result in body["results"])
    assert body["llm_execution"]["provider"] == "deepseek"
    assert body["llm_execution"]["model"] == "deepseek-v4-flash"
    assert body["llm_execution"]["attempted_calls"] >= 20
    assert body["llm_execution"]["successful_calls"] == body["llm_execution"]["attempted_calls"]
    assert body["llm_execution"]["failed_calls"] == 0
    assert body["llm_execution"]["fallback_calls"] == 0

    latest = client.get("/api/evals/latest").json()
    assert latest["run_id"] == body["run_id"]
    assert api_key not in json.dumps(latest)


def test_chinese_real_eval_audit_and_results_do_not_contain_key(client, monkeypatch):
    def fake_request(self: DeepSeekLLMClient, body: dict) -> str:
        del self
        prompt = body["messages"][0]["content"]
        if "Return JSON" in prompt:
            return json.dumps(
                {
                    "category": "模型建议",
                    "priority": "高",
                    "risk_level": "中",
                    "requires_human": True,
                    "requires_approval": True,
                    "confidence": 0.99,
                },
                ensure_ascii=False,
            )
        return "感谢您联系我们。我已根据相关政策核对该请求，并将以中文说明安全的后续处理步骤。"

    monkeypatch.setattr(DeepSeekLLMClient, "_request_once", fake_request)
    api_key = "sk-chinese-eval-secret-test"

    response = client.post(
        "/api/evals/run?locale=zh",
        headers={"X-DeepSeek-API-Key": api_key},
    )

    assert response.status_code == 200
    assert api_key not in response.text
    body = response.json()
    assert body["failed_cases"] == []
    assert all(result["llm_ok"] for result in body["results"])
    assert all(result["response_language_ok"] for result in body["results"])
    assert all(result["llm_calls"]["successful_calls"] >= 1 for result in body["results"])
    assert body["llm_execution"]["failed_calls"] == 0
    assert body["llm_execution"]["fallback_calls"] == 0
    assert api_key not in LATEST_RESULTS_PATHS["zh"].read_text(encoding="utf-8")
