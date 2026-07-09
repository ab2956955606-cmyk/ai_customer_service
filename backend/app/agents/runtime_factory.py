from __future__ import annotations

import os

from app.agents.custom_runner import CustomSupportRunner


def get_support_runner():
    runtime = os.getenv("SUPPORT_AGENT_RUNTIME", "custom").strip().lower()
    if runtime == "langgraph":
        from app.agents.langgraph_runner import LangGraphSupportRunner

        return LangGraphSupportRunner()
    return CustomSupportRunner()
