from __future__ import annotations

import json
import re
import socket
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any

from app.agents.policy import detect_locale, deterministic_classification
from app.config import get_settings

CANONICAL_CATEGORIES = {
    "account",
    "billing",
    "fraud",
    "security",
    "shipping",
    "technical",
    "general",
    "unknown",
}
CANONICAL_PRIORITIES = {"normal", "medium", "urgent"}
CANONICAL_RISK_LEVELS = {"low", "medium", "high"}


class BaseLLMClient:
    provider_name = "mock"
    model_name = "deterministic"

    def __init__(self) -> None:
        self.attempted_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0
        self.fallback_calls = 0
        self.retry_attempts = 0
        self.last_classification_suggestion: dict[str, Any] | None = None

    def classify_ticket(self, subject: str, description: str) -> dict[str, Any]:
        raise NotImplementedError

    def draft_response(self, state: dict[str, Any]) -> str:
        raise NotImplementedError

    def record_fallback(self) -> None:
        self.fallback_calls += 1

    def call_audit(self) -> dict[str, str | int]:
        return {
            "provider": self.provider_name,
            "model": self.model_name,
            "attempted_calls": self.attempted_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "fallback_calls": self.fallback_calls,
            "retry_attempts": self.retry_attempts,
        }


class MockLLMClient(BaseLLMClient):
    def classify_ticket(self, subject: str, description: str) -> dict[str, Any]:
        return deterministic_classification(subject, description)

    def draft_response(self, state: dict[str, Any]) -> str:
        citations = state.get("citations") or []
        locale = state.get("locale") or detect_locale(
            str(state.get("subject", "")),
            str(state.get("sanitized_description") or state.get("description", "")),
        )
        if locale == "zh":
            if state.get("requires_human"):
                return "该工单包含高风险信息，已转交人工客服专员审查，我们会尽快与您联系。"
            if state.get("low_confidence"):
                return "请补充说明您遇到的具体问题、期望结果以及相关订单或账户信息，以便我们准确处理。"

            subject = state.get("subject", "您的请求")
            if citations:
                sources = "、".join(c["title"] for c in citations)
                return f"感谢您联系我们处理“{subject}”。我已核对相关政策，可以协助您完成后续步骤。参考来源：{sources}。"
            return f"感谢您联系我们处理“{subject}”。我们正在确认最合适的后续处理方式。"

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

class OpenAICompatibleLLMClient(MockLLMClient):
    provider_name = "openai_compatible"

    def __init__(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        request_overrides: dict[str, Any] | None = None,
        fallback_on_error: bool = True,
        max_retries: int = 0,
    ) -> None:
        super().__init__()
        settings = get_settings()
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.base_url = base_url or settings.openai_base_url
        self.model = model or settings.openai_model
        self.model_name = self.model
        self.request_overrides = request_overrides or {}
        self.fallback_on_error = fallback_on_error
        self.max_retries = max_retries

    def classify_ticket(self, subject: str, description: str) -> dict[str, Any]:
        baseline = super().classify_ticket(subject, description)
        prompt = (
            "Return JSON with category, priority, risk_level, requires_human, "
            "requires_approval, and confidence. "
            f"Allowed categories: {sorted(CANONICAL_CATEGORIES)}. "
            f"Allowed priorities: {sorted(CANONICAL_PRIORITIES)}. "
            f"Allowed risk levels: {sorted(CANONICAL_RISK_LEVELS)}.\n"
            f"Subject: {subject}\nDescription: {description}"
        )
        try:
            data = self._chat(prompt, response_format={"type": "json_object"})
            parsed = self._parse_classification(data)
            self.last_classification_suggestion = parsed
            return baseline
        except Exception:
            if not self.fallback_on_error:
                raise
            self.record_fallback()
            return baseline

    def draft_response(self, state: dict[str, Any]) -> str:
        try:
            locale = state.get("locale") or detect_locale(
                str(state.get("subject", "")),
                str(state.get("sanitized_description") or state.get("description", "")),
            )
            language_instruction = (
                "Reply in Simplified Chinese. Keep policy filenames and order IDs unchanged."
                if locale == "zh"
                else "Reply in English."
            )
            context = "\n".join(
                f"- {citation['title']}: {citation.get('snippet', '')}"
                for citation in state.get("citations", [])
            )
            return self._chat(
                "Draft a concise customer support response grounded only in the supplied ticket and policy context. "
                f"{language_instruction}\n"
                f"Category: {state.get('category')}\n"
                f"Subject: {state.get('subject')}\n"
                f"Description: {state.get('sanitized_description') or state.get('description')}\n"
                f"Policy context:\n{context or '- No matching policy context.'}"
            )
        except Exception:
            if not self.fallback_on_error:
                raise
            self.record_fallback()
            return super().draft_response(state)

    @staticmethod
    def _parse_classification(content: str) -> dict[str, Any]:
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if not match:
            raise RuntimeError("LLM returned no classification JSON")
        parsed = json.loads(match.group(0))
        if not isinstance(parsed, dict):
            raise RuntimeError("LLM classification JSON must be an object")
        allowed_keys = {
            "category",
            "priority",
            "risk_level",
            "requires_human",
            "requires_approval",
            "confidence",
        }
        return {key: parsed[key] for key in parsed.keys() & allowed_keys}

    def _chat(self, prompt: str, response_format: dict[str, str] | None = None) -> str:
        if not self.api_key:
            raise RuntimeError("LLM API key is not configured")
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            **self.request_overrides,
        }
        if response_format:
            body["response_format"] = response_format

        self.attempted_calls += 1
        try:
            content = self._request_with_retries(body)
        except Exception:
            self.failed_calls += 1
            raise
        self.successful_calls += 1
        return content

    def _request_with_retries(self, body: dict[str, Any]) -> str:
        for retry_index in range(self.max_retries + 1):
            try:
                return self._request_once(body)
            except urllib.error.HTTPError as exc:
                transient = exc.code == 429 or 500 <= exc.code <= 599
                if transient and retry_index < self.max_retries:
                    self.retry_attempts += 1
                    time.sleep(self._retry_delay(exc, retry_index))
                    continue
                raise RuntimeError(f"LLM request failed with HTTP status {exc.code}") from exc
            except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
                if retry_index < self.max_retries:
                    self.retry_attempts += 1
                    time.sleep(min(2**retry_index, 5))
                    continue
                raise RuntimeError("LLM request failed because of a network error") from exc
        raise RuntimeError("LLM request failed after retries")

    @staticmethod
    def _retry_delay(exc: urllib.error.HTTPError, retry_index: int) -> float:
        retry_after = exc.headers.get("Retry-After") if exc.headers else None
        try:
            return min(max(float(retry_after), 0), 5) if retry_after else min(2**retry_index, 5)
        except ValueError:
            return min(2**retry_index, 5)

    def _request_once(self, body: dict[str, Any]) -> str:
        request = urllib.request.Request(
            f"{self.base_url.rstrip('/')}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload["choices"][0]["message"]["content"]

    def clear_credentials(self) -> None:
        self.api_key = None


class DeepSeekLLMClient(OpenAICompatibleLLMClient):
    provider_name = "deepseek"

    def __init__(self, api_key: str) -> None:
        if not api_key.strip():
            raise ValueError("DeepSeek API key cannot be empty")
        super().__init__(
            api_key=api_key.strip(),
            base_url="https://api.deepseek.com",
            model="deepseek-v4-flash",
            request_overrides={"thinking": {"type": "disabled"}},
            fallback_on_error=False,
            max_retries=2,
        )


_REQUEST_LLM_CLIENT: ContextVar[BaseLLMClient | None] = ContextVar(
    "supportops_request_llm_client",
    default=None,
)


@contextmanager
def temporary_llm_client(client: OpenAICompatibleLLMClient) -> Iterator[None]:
    token = _REQUEST_LLM_CLIENT.set(client)
    try:
        yield
    finally:
        _REQUEST_LLM_CLIENT.reset(token)
        client.clear_credentials()


def get_llm_client() -> BaseLLMClient:
    request_client = _REQUEST_LLM_CLIENT.get()
    if request_client is not None:
        return request_client
    provider = get_settings().llm_provider.lower()
    if provider == "openai_compatible":
        return OpenAICompatibleLLMClient()
    return MockLLMClient()
