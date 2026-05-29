"""OpenAI-compatible client pointed at OpenRouter.

Single seam between the bot core and any language model provider.
If we ever want to swap to direct Anthropic for prompt caching wins,
this is the file that changes.

The model used is configurable through the `BOT_MODEL` environment
variable. `MODEL_EXAMPLES` lists curated identifiers across the
providers we've found worth trying — OpenRouter's catalogue at
https://openrouter.ai/models is authoritative; identifiers churn.
Tool-use quality varies a lot: Claude and Gemini Pro call tools
reliably, smaller models sometimes skip the tool and hallucinate SQL
results, which the SQL guard catches but answers degrade visibly.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI


DEFAULT_MODEL = "anthropic/claude-sonnet-4.6"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

# Curated BOT_MODEL examples grouped by provider. Each entry is
# (openrouter slug, short note). Not exhaustive; not pinned.
MODEL_EXAMPLES: Dict[str, List[Tuple[str, str]]] = {
    "Claude (Anthropic)": [
        (
            "anthropic/claude-sonnet-4.6",
            "default — balanced reasoning, reliable tool use",
        ),
        (
            "anthropic/claude-opus-4-7",
            "top-tier reasoning; slower and costlier",
        ),
        (
            "anthropic/claude-haiku-4-5",
            "fastest Claude tier; good for cheap experiments",
        ),
    ],
    "Gemini (Google)": [
        (
            "google/gemini-2.5-pro",
            "Google's strongest; competitive tool use",
        ),
        (
            "google/gemini-2.5-flash",
            "fast and cheap; lighter tool reliability",
        ),
    ],
    "Mistral": [
        (
            "mistralai/mistral-large-2411",
            "general-purpose flagship",
        ),
        (
            "mistralai/codestral-2501",
            "code-leaning; may shine on SQL specifically",
        ),
    ],
    "DeepSeek": [
        (
            "deepseek/deepseek-r1",
            "reasoning-focused; can over-think simple queries",
        ),
        (
            "deepseek/deepseek-chat",
            "general chat; cheap; verify tool calls in practice",
        ),
    ],
}


def model_name() -> str:
    return os.environ.get("BOT_MODEL", DEFAULT_MODEL)


def supports_anthropic_caching(model: Optional[str] = None) -> bool:
    """Anthropic requires an explicit `cache_control` marker; other
    providers either auto-cache or do not yet support it via OpenRouter.
    OpenRouter passes the marker through to direct Anthropic
    (see https://openrouter.ai/docs/guides/best-practices/prompt-caching).
    """
    return (model or model_name()).lower().startswith("anthropic/")


def system_message(text: str, *, model: Optional[str] = None) -> dict:
    """Build a `system` message. For Anthropic models, wrap the text in
    a content block with `cache_control: ephemeral` so the (large,
    near-stable) system prompt is served from Anthropic's prefix cache
    on subsequent turns. Other providers get the plain-string shape
    OpenAI's spec expects.
    """
    if supports_anthropic_caching(model):
        return {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": text,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
        }
    return {"role": "system", "content": text}


def _client() -> OpenAI:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY is not set")
    base = os.environ.get("OPENROUTER_BASE_URL", DEFAULT_BASE_URL)
    return OpenAI(base_url=base, api_key=key)


def chat(
    messages: List[dict],
    tools: Optional[List[dict]] = None,
    **kwargs: Any,
):
    """Call the configured OpenRouter model with messages and (optional) tools."""
    client = _client()
    return client.chat.completions.create(
        model=model_name(),
        messages=messages,
        tools=tools,
        **kwargs,
    )
