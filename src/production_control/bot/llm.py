"""OpenAI-compatible client pointed at OpenRouter.

Single seam between the bot core and any language model provider.
If we ever want to swap to direct Anthropic for prompt caching wins,
this is the file that changes.
"""

from __future__ import annotations

import os
from typing import Any, List, Optional

from openai import OpenAI


DEFAULT_MODEL = "anthropic/claude-sonnet-4.6"
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"


def model_name() -> str:
    return os.environ.get("BOT_MODEL", DEFAULT_MODEL)


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
