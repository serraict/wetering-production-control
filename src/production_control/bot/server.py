"""FastAPI app exposing the bot to Zulip via the outgoing-webhook protocol.

Zulip POSTs a JSON payload to `/zulip` when the bot is @-mentioned in
a stream or DM'd; we reply synchronously with `{"content": "..."}`
which Zulip then posts in the same stream/topic or DM thread. We
speak the HTTP protocol directly — the `zulip` Python library is not
imported.

Slice 3 (ADR-0002 §7): per-`(stream, topic)` (or per-DM-sender)
multi-turn memory lives here. `bot.conversation` owns the store;
this module derives the key from the payload, threads history into
`bot.answer`, and persists the new turn back. `@bot reset` clears
the current key's history.
"""

from __future__ import annotations

import os
import re
import secrets
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, status

from production_control.bot import answer as answer_mod
from production_control.bot import conversation
from production_control.bot.zulip_payload import (
    ZulipMessage,
    ZulipWebhookPayload,
    strip_mention,
)

TOKEN_ENV_VAR = "ZULIP_OUTGOING_WEBHOOK_TOKEN"

_RESET_RE = re.compile(r"^/?reset\s*$", re.IGNORECASE)
_RESET_ACK = "Context gewist; we beginnen opnieuw."

app = FastAPI(title="Wetering insights bot")


def _verify_token(provided: str) -> None:
    expected = os.environ.get(TOKEN_ENV_VAR, "")
    if not expected or not secrets.compare_digest(expected, provided):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid Zulip outgoing-webhook token",
        )


def _conversation_key(message: Optional[ZulipMessage]) -> Optional[str]:
    """Derive a stable per-conversation key from the Zulip message.

    Stream messages are keyed by (stream_id, topic); DMs by sender
    email. If the payload lacks the fields we need (e.g. older tests
    that only set `type`), returns None — caller falls back to a
    memory-less call.
    """
    if message is None:
        return None
    if message.type == "stream" and message.stream_id is not None and message.subject:
        return f"stream:{message.stream_id}:{message.subject}"
    if message.type == "private" and message.sender_email:
        return f"dm:{message.sender_email}"
    return None


def _format_reply(result: answer_mod.AnswerResult) -> str:
    """Compose the body Zulip will post: text + SQL echo + footer."""
    parts = [result.text]
    if result.sql:
        parts.append(f"```sql\n{result.sql[-1]}\n```")
    parts.append(answer_mod.footer(result))
    return "\n\n".join(parts)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/zulip")
def zulip_webhook(payload: ZulipWebhookPayload) -> Dict[str, Any]:
    _verify_token(payload.token)
    question = strip_mention(payload.data, payload.bot_full_name)
    if not question:
        # Empty JSON body is Zulip's "no reply" convention.
        return {}

    key = _conversation_key(payload.message)

    if _RESET_RE.match(question):
        if key:
            conversation.reset(key)
        return {"content": _RESET_ACK}

    history = conversation.recall(key) if key else []
    result = answer_mod.answer(question, history=history)
    if key and not result.error:
        conversation.extend(key, result.new_messages, result.tokens)

    return {"content": _format_reply(result)}
