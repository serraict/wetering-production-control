"""FastAPI app exposing the bot to Zulip via the outgoing-webhook protocol.

Zulip POSTs a JSON payload to `/zulip` when the bot is @-mentioned in
a stream or DM'd; we reply synchronously with `{"content": "..."}`
which Zulip then posts in the same stream/topic or DM thread. We
speak the HTTP protocol directly — the `zulip` Python library is not
imported.

Stateless v1 (ADR-0002): every request is independent. Per-topic
conversation memory is slice 3.
"""

from __future__ import annotations

import os
import secrets
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, status

from production_control.bot import answer as answer_mod
from production_control.bot.zulip_payload import ZulipWebhookPayload, strip_mention

TOKEN_ENV_VAR = "ZULIP_OUTGOING_WEBHOOK_TOKEN"

app = FastAPI(title="Wetering insights bot")


def _verify_token(provided: str) -> None:
    expected = os.environ.get(TOKEN_ENV_VAR, "")
    if not expected or not secrets.compare_digest(expected, provided):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid Zulip outgoing-webhook token",
        )


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
    result = answer_mod.answer(question)
    body = result.text + "\n\n" + answer_mod.footer(result)
    return {"content": body}
