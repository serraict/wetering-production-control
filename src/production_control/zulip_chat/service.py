"""High-level Zulip operations for lot conversations.

The web layer only depends on this module — it never imports the Zulip SDK
directly. The service returns plain dataclasses and never raises into the UI;
callers get a `ZulipServiceError` on any failure.
"""

from __future__ import annotations

import logging
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, List, Optional

from ..config.zulip_config import ZulipConfig, get_zulip_config
from .client import ZulipClient, ZulipClientError, get_client
from .topics import topic_name_for

logger = logging.getLogger(__name__)


class ZulipServiceError(RuntimeError):
    """Raised by the service when an operation cannot be completed."""


@dataclass
class ZulipMessage:
    """A single message in a lot's topic."""

    id: int
    sender_full_name: str
    timestamp: datetime
    content_html: str  # Zulip's server-rendered, sanitized HTML


def _to_message(raw: Any) -> ZulipMessage:
    ts = raw.get("timestamp")
    when = (
        datetime.fromtimestamp(int(ts), tz=timezone.utc)
        if ts is not None
        else datetime.now(tz=timezone.utc)
    )
    return ZulipMessage(
        id=int(raw["id"]),
        sender_full_name=raw.get("sender_full_name", "Unknown"),
        timestamp=when,
        content_html=raw.get("content", ""),
    )


def _client_and_config(
    client: Optional[ZulipClient], config: Optional[ZulipConfig]
) -> tuple[ZulipClient, ZulipConfig]:
    return client or get_client(), config or get_zulip_config()


def get_messages(
    lot: Any,
    *,
    client: Optional[ZulipClient] = None,
    config: Optional[ZulipConfig] = None,
) -> List[ZulipMessage]:
    """Return the recent messages for `lot`'s topic, oldest first."""
    cli, cfg = _client_and_config(client, config)
    topic = topic_name_for(lot)
    try:
        raw_messages = cli.get_messages_in_topic(
            cfg.stream, topic, cfg.message_history_limit
        )
    except ZulipClientError as e:
        raise ZulipServiceError(str(e)) from e
    return [_to_message(m) for m in raw_messages]


def post(
    lot: Any,
    content: str,
    *,
    user_name: str = "Guest",
    client: Optional[ZulipClient] = None,
    config: Optional[ZulipConfig] = None,
) -> int:
    """Post `content` to `lot`'s topic, attributed to `user_name`.

    The Zulip account is the bot — we prepend `**{user_name}**: ` to keep the
    human author visible in every message.
    """
    text = content.strip()
    if not text:
        raise ZulipServiceError("Cannot post an empty message")
    attributed = f"**{user_name}**: {text}"
    cli, cfg = _client_and_config(client, config)
    topic = topic_name_for(lot)
    try:
        return cli.send_message(cfg.stream, topic, attributed)
    except ZulipClientError as e:
        raise ZulipServiceError(str(e)) from e


def narrow_url(
    lot: Any, *, config: Optional[ZulipConfig] = None
) -> str:
    """Return a URL into the Zulip web client narrowed to this lot's topic."""
    cfg = config or get_zulip_config()
    if not cfg.site:
        return ""
    stream = urllib.parse.quote(cfg.stream, safe="")
    topic = urllib.parse.quote(topic_name_for(lot), safe="")
    site = cfg.site.rstrip("/")
    return f"{site}/#narrow/stream/{stream}/topic/{topic}"
