"""Pydantic models + helpers for Zulip outgoing-webhook payloads.

Zulip POSTs JSON to our endpoint when the bot is @-mentioned in a
stream or DM'd. We only model the fields we actually consume:
`token` (for verification), `bot_full_name` (for mention stripping),
and `data` (the raw message). All other Zulip fields are accepted and
ignored — Zulip evolves the payload over time and we don't want to
become brittle to additions.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ZulipMessage(BaseModel):
    """The nested `message` object Zulip sends. v1 only inspects `type`."""

    model_config = ConfigDict(extra="ignore")

    type: str = Field(default="stream")  # "stream" or "private"


class ZulipWebhookPayload(BaseModel):
    """Top-level outgoing-webhook POST body."""

    model_config = ConfigDict(extra="ignore")

    token: str
    bot_full_name: str
    data: str
    message: Optional[ZulipMessage] = None


def strip_mention(text: str, bot_full_name: str) -> str:
    """Strip a leading `@**Bot**` or `@_**Bot**` mention from `text`.

    Returns the rest of the message (whitespace-trimmed). If no mention
    is at the start (typical for DMs), returns the trimmed input
    unchanged. Only a single mention at the start is stripped.
    """
    s = text.lstrip()
    prefixes = (f"@**{bot_full_name}**", f"@_**{bot_full_name}**")
    for prefix in prefixes:
        if s.startswith(prefix):
            return s[len(prefix) :].strip()
    return s.strip()
