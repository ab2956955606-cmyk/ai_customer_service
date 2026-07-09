from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from typing import Any

from app.config import get_settings


URGENT_TERMS = {
    "fraud",
    "unauthorized charge",
    "chargeback",
    "hacked",
    "account takeover",
    "legal",
    "lawsuit",
    "police",
    "emergency",
}


class BaseLLMClient:
    def classify_ticket(self, subject: str, description: str) -> dict[str, Any]:
        raise NotImplementedError

    def draft_response(self, state: dict[str, Any]) -> str:
        raise NotImplementedError


class MockLLMClient(BaseLLMClient):
    def classify_ticket(self, subject: str, description: str) -> dict[str, Any]:
        text = f"{subject} {description}".lower()
        if any(term in text for term in URGENT_TERMS):
            category = "fraud" if any(term in text for term in {"fraud", "unauthorized charge", "chargeback"}) else "security"
            return {
                "category": category,
                "priority": "urgent",
                "risk_level": "high",
                "requires_human": True,
                "requires_approval": False,
                "confidence": 0.96,
            }
        if "refund" in text or "money back" in text or "duplicate charge" in text:
            return self._result("billing", "medium", "medium", approval=True, confidence=0.9)
        if "address" in text or "shipping" in text or "shipment" in text or "delivery" in text:
            approval = "change" in text or "update" in text or "new address" in text
            return self._result("shipping", "medium" if approval else "normal", "medium" if approval else "low", approval=approval, confidence=0.88)
        if "cancel order" in text:
            return self._result("shipping", "medium", "medium", approval=True, confidence=0.9)
        if "cancel subscription" in text or "subscription" in text or "downgrade" in text:
            approval = "downgrade" in text or "delete" in text
            return self._result("account", "normal", "medium" if approval else "low", approval=approval, confidence=0.86)
        if "password" in text or "reset" in text or "login" in text or "sign in" in text:
            return self._result("account", "normal", "low", confidence=0.92)
        if "invoice" in text or "receipt" in text or "tax" in text:
            return self._result("billing", "normal", "low", confidence=0.9)
        if "setup" in text or "install" in text or "configure" in text:
            return self._result("technical", "normal", "low", confidence=0.84)
        if "angry" in text or "terrible" in text or "unacceptable" in text:
            return self._result("general", "medium", "low", confidence=0.7)
        return self._result("unknown", "normal", "low", confidence=0.35)

    def draft_response(self, state: dict[str, Any]) -> str:
        citations = state.get("citations") or []
        if state.get("requires_human"):
            return "A human support specialist will review this case because it includes high-risk language."
        if state.get("low_confidence"):
            return "Could you share a little more detail so we can route this to the right support path?"

        subject = state.get("subject", "your request")
        if citations:
            sources = ", ".join(c["title"] for c in citations)
            return (
                f"Thanks for contacting support about {subject}. I checked the relevant policy and "
                f"can help with the next steps. Sources: {sources}."
            )
        return f"Thanks for contacting support about {subject}. We are reviewing the next best step."

    @staticmethod
    def _result(
        category: str,
        priority: str,
        risk_level: str,
        approval: bool = False,
        confidence: float = 0.8,
    ) -> dict[str, Any]:
        return {
            "category": category,
            "priority": priority,
            "risk_level": risk_level,
            "requires_human": False,
            "requires_approval": approval,
            "confidence": confidence,
        }


class OpenAICompatibleLLMClient(MockLLMClient):
    def __init__(self) -> None:
        self.settings = get_settings()

    def classify_ticket(self, subject: str, description: str) -> dict[str, Any]:
        prompt = (
            "Return JSON with category, priority, risk_level, requires_human, "
            f"requires_approval, confidence for this support ticket:\nSubject: {subject}\nDescription: {description}"
        )
        try:
            data = self._chat(prompt)
            match = re.search(r"\{.*\}", data, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                fallback = super().classify_ticket(subject, description)
                fallback.update({k: parsed[k] for k in parsed.keys() & fallback.keys()})
                return fallback
        except Exception:
            return super().classify_ticket(subject, description)
        return super().classify_ticket(subject, description)

    def draft_response(self, state: dict[str, Any]) -> str:
        try:
            citations = ", ".join(c["title"] for c in state.get("citations", []))
            return self._chat(
                "Draft a concise customer support response. "
                f"Category: {state.get('category')}. Subject: {state.get('subject')}. Sources: {citations}."
            )
        except Exception:
            return super().draft_response(state)

    def _chat(self, prompt: str) -> str:
        if not self.settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured")
        body = {
            "model": self.settings.openai_model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
        }
        request = urllib.request.Request(
            f"{self.settings.openai_base_url.rstrip('/')}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.openai_api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.URLError as exc:
            raise RuntimeError(f"LLM request failed: {exc}") from exc
        return payload["choices"][0]["message"]["content"]


def get_llm_client() -> BaseLLMClient:
    provider = get_settings().llm_provider.lower()
    if provider == "openai_compatible":
        return OpenAICompatibleLLMClient()
    return MockLLMClient()
