from __future__ import annotations

from app.agents.custom_runner import CustomSupportRunner
from app.agents.runtime_factory import get_support_runner


def test_runtime_factory_defaults_to_custom(monkeypatch):
    monkeypatch.delenv("SUPPORT_AGENT_RUNTIME", raising=False)
    assert isinstance(get_support_runner(), CustomSupportRunner)


def test_runtime_factory_invalid_value_falls_back_to_custom(monkeypatch):
    monkeypatch.setenv("SUPPORT_AGENT_RUNTIME", "unknown")
    assert isinstance(get_support_runner(), CustomSupportRunner)
