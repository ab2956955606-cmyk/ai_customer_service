from __future__ import annotations

import json
import urllib.error

import pytest

from app.agents.llm import DeepSeekLLMClient


def test_deepseek_key_is_request_scoped(client, monkeypatch):
    calls: list[dict[str, str | None]] = []

    def fake_request(self: DeepSeekLLMClient, body: dict) -> str:
        prompt = body["messages"][0]["content"]
        calls.append(
            {
                "api_key": self.api_key,
                "base_url": self.base_url,
                "model": self.model,
            }
        )
        if "Return JSON" in prompt:
            return json.dumps(
                {
                    "category": "Account Access",
                    "priority": "High",
                    "risk_level": "Medium",
                    "requires_human": False,
                    "requires_approval": False,
                    "confidence": 0.95,
                }
            )
        return "DeepSeek drafted this response from the retrieved policy."

    monkeypatch.setattr(DeepSeekLLMClient, "_request_once", fake_request)
    api_key = "sk-ephemeral-test-key"
    response = client.post(
        "/api/tickets",
        headers={"X-DeepSeek-API-Key": api_key},
        json={
            "subject": "Cannot reset password",
            "description": "The reset link is not arriving in my email.",
            "customer_email": "alice@example.com",
        },
    )

    assert response.status_code == 200
    assert api_key not in response.text
    assert len(calls) == 2
    assert all(call["api_key"] == api_key for call in calls)
    assert all(call["base_url"] == "https://api.deepseek.com" for call in calls)
    assert all(call["model"] == "deepseek-v4-flash" for call in calls)
    assert "DeepSeekLLMClient" in {
        event["tool_name"] for event in response.json()["events"]
    }
    body = response.json()
    assert body["ticket"]["category"] == "account"
    assert body["ticket"]["priority"] == "normal"
    assert body["ticket"]["risk_level"] == "low"
    triage = next(event for event in body["events"] if event["node_name"] == "triage_agent_node")
    assert "LLM suggested category=Account Access" in triage["output_summary"]
    assert "Python policy enforced category=account" in triage["output_summary"]

    calls.clear()
    mock_response = client.post(
        "/api/tickets",
        json={
            "subject": "Need invoice",
            "description": "Please help me find my invoice.",
            "customer_email": "alice@example.com",
        },
    )
    assert mock_response.status_code == 200
    assert calls == []
    assert "MockLLMClient" in {
        event["tool_name"] for event in mock_response.json()["events"]
    }


@pytest.mark.parametrize(
    "suggestion",
    [
        {
            "category": "Account Access",
            "priority": "High",
            "risk_level": "Medium",
            "requires_human": False,
            "requires_approval": False,
            "confidence": 0.95,
        },
        {
            "category": "LOGIN",
            "priority": "NORMAL",
            "risk_level": "LOW",
            "requires_human": False,
            "requires_approval": False,
            "confidence": 0.95,
        },
        {
            "category": "not-a-category",
            "priority": "P0",
            "risk_level": "catastrophic",
            "requires_human": True,
            "requires_approval": True,
            "confidence": 0.99,
        },
    ],
    ids=["synonyms", "case-variants", "invalid-enums"],
)
def test_model_enum_variants_cannot_override_deterministic_policy(monkeypatch, suggestion):
    client = DeepSeekLLMClient("sk-enum-test")
    monkeypatch.setattr(client, "_request_once", lambda body: json.dumps(suggestion))

    result = client.classify_ticket(
        "Cannot reset password",
        "The reset link is not arriving in my email.",
    )

    assert result == {
        "category": "account",
        "priority": "normal",
        "risk_level": "low",
        "requires_human": False,
        "requires_approval": False,
        "confidence": 0.92,
    }
    assert client.last_classification_suggestion == suggestion


def test_deepseek_retries_transient_errors(monkeypatch):
    client = DeepSeekLLMClient("sk-retry-test")
    attempts = 0

    def flaky_request(body: dict) -> str:
        nonlocal attempts
        del body
        attempts += 1
        if attempts == 1:
            raise urllib.error.HTTPError(
                url="https://api.deepseek.com/chat/completions",
                code=429,
                msg="rate limited",
                hdrs={},
                fp=None,
            )
        return json.dumps(
            {
                "category": "account",
                "priority": "normal",
                "risk_level": "low",
                "requires_human": False,
                "requires_approval": False,
                "confidence": 0.9,
            }
        )

    monkeypatch.setattr(client, "_request_once", flaky_request)
    monkeypatch.setattr("app.agents.llm.time.sleep", lambda _: None)

    result = client.classify_ticket("Password reset", "Reset email missing")

    assert result["category"] == "account"
    assert attempts == 2
    assert client.call_audit()["attempted_calls"] == 1
    assert client.call_audit()["successful_calls"] == 1
    assert client.call_audit()["failed_calls"] == 0
    assert client.call_audit()["retry_attempts"] == 1


def test_deepseek_does_not_retry_authentication_errors(monkeypatch):
    client = DeepSeekLLMClient("sk-auth-test")
    attempts = 0

    def rejected_request(body: dict) -> str:
        nonlocal attempts
        del body
        attempts += 1
        raise urllib.error.HTTPError(
            url="https://api.deepseek.com/chat/completions",
            code=401,
            msg="unauthorized",
            hdrs={},
            fp=None,
        )

    monkeypatch.setattr(client, "_request_once", rejected_request)

    with pytest.raises(RuntimeError, match="HTTP status 401"):
        client.classify_ticket("Password reset", "Reset email missing")

    assert attempts == 1
    assert client.call_audit()["failed_calls"] == 1
    assert client.call_audit()["retry_attempts"] == 0
