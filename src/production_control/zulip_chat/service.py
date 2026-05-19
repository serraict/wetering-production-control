"""High-level Zulip operations for lot conversations.

The web layer only depends on this module — it never imports the Zulip SDK
directly. The service returns plain dataclasses and never raises into the UI;
callers get a `ZulipServiceError` on any failure.
"""

from __future__ import annotations

import logging
import re
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, List, Optional, Tuple

from ..config.zulip_config import ZulipConfig, get_zulip_config
from .client import ZulipClient, ZulipClientError, get_client
from .topics import topic_name_for

logger = logging.getLogger(__name__)


class ZulipServiceError(RuntimeError):
    """Raised by the service when an operation cannot be completed."""


@dataclass
class ZulipMessage:
    """A single message in a lot's topic.

    `sender_full_name` / `content_html` are the raw values returned by Zulip
    (the sender is the bot account in our setup). `author_name` and
    `body_html` are the human author and body after stripping the
    `**name**: ` prefix that `post()` adds; if the prefix isn't present they
    fall back to the bot's name and the full body.
    """

    id: int
    sender_full_name: str
    timestamp: datetime
    content_html: str
    author_name: str
    body_html: str


# Matches Zulip's rendering of `**name**: rest`, which looks like:
#   <p><strong>name</strong>: rest…</p>
_AUTHOR_PREFIX_RE = re.compile(
    r"^\s*<p>\s*<strong>(?P<author>[^<]+)</strong>\s*:\s*(?P<rest>.*)$",
    flags=re.DOTALL,
)


def _split_author_prefix(content_html: str) -> Tuple[Optional[str], str]:
    """Pull the leading `**author**: ` prefix out of a rendered message."""
    match = _AUTHOR_PREFIX_RE.match(content_html)
    if not match:
        return None, content_html
    return match.group("author").strip() or None, "<p>" + match.group("rest")


def _absolutize_uploads(html: str, site: str) -> str:
    """Rewrite relative `/user_uploads/...` URLs to absolute against `site`."""
    if not site or "/user_uploads/" not in html:
        return html
    prefix = site.rstrip("/")
    return html.replace('"/user_uploads/', f'"{prefix}/user_uploads/')


def _to_message(raw: Any, *, site: str = "") -> ZulipMessage:
    ts = raw.get("timestamp")
    when = (
        datetime.fromtimestamp(int(ts), tz=timezone.utc)
        if ts is not None
        else datetime.now(tz=timezone.utc)
    )
    sender = raw.get("sender_full_name", "Unknown")
    content_html = _absolutize_uploads(raw.get("content", ""), site)
    author, body_html = _split_author_prefix(content_html)
    return ZulipMessage(
        id=int(raw["id"]),
        sender_full_name=sender,
        timestamp=when,
        content_html=content_html,
        author_name=author or sender,
        body_html=body_html,
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
    return [_to_message(m, site=cfg.site) for m in raw_messages]


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
