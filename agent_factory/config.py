"""Model configuration for both the meta-agent and the crews it generates.

CrewAI 1.x ships a native Anthropic provider (it calls the official `anthropic`
SDK directly, not a shim), selected by the `anthropic/` prefix on the model id.

Two deliberate choices:

* `thinking` is left unset. On Claude Opus 5 adaptive thinking is on by default,
  and CrewAI's `AnthropicThinkingConfig` only models the legacy
  `{"type": "enabled", "budget_tokens": N}` shape, which Opus 5 rejects with a 400.
* `max_tokens` is set explicitly. The provider would otherwise default to the
  model's 128K ceiling, and CrewAI calls the Messages API without streaming —
  a combination that invites HTTP timeouts.
"""

from __future__ import annotations

import os

from crewai import LLM

__all__ = ["ARCHITECT_MODEL", "WORKER_MODEL", "build_llm", "require_api_key"]

# The architect designs crews; that is the reasoning-heavy job, so it gets Opus.
ARCHITECT_MODEL = os.environ.get("AGENT_FACTORY_ARCHITECT_MODEL", "anthropic/claude-opus-5")
# Generated crews default to the same model unless the caller overrides it.
WORKER_MODEL = os.environ.get("AGENT_FACTORY_WORKER_MODEL", "anthropic/claude-opus-5")


def build_llm(model: str = ARCHITECT_MODEL, *, max_tokens: int = 16000) -> LLM:
    """Construct a CrewAI LLM bound to Anthropic's native provider."""
    return LLM(model=model, max_tokens=max_tokens)


def require_api_key() -> None:
    """Fail early with a useful message rather than deep inside a crew run."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Either put it in a .env file next to "
            "main.py:\n"
            "    cp .env.example .env     # then edit in your key\n"
            "or export it for this shell:\n"
            "    export ANTHROPIC_API_KEY=sk-ant-...\n"
            "Keys come from https://console.anthropic.com/settings/keys"
        )
