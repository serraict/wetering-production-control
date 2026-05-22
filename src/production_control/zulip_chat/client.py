"""Thin wrapper over the Zulip Python SDK."""

from __future__ import annotations

import logging
from threading import Lock
from typing import Any, Dict, List, Optional

import zulip

from ..config.zulip_config import ZulipConfig, get_zulip_config

logger = logging.getLogger(__name__)


class ZulipClientError(RuntimeError):
    """Raised when the Zulip SDK reports an error or the call fails."""


class ZulipClient:
    """Lazy, reusable wrapper around `zulip.Client`."""

    def __init__(self, config: Optional[ZulipConfig] = None) -> None:
        self._config = config
        self._client: Optional[zulip.Client] = None
        self._lock = Lock()

    @property
    def config(self) -> ZulipConfig:
        return self._config or get_zulip_config()

    def _get_sdk(self) -> zulip.Client:
        with self._lock:
            if self._client is None:
                cfg = self.config
                if not (cfg.site and cfg.bot_email and cfg.bot_api_key):
                    raise ZulipClientError(
                        "Zulip is not configured (ZULIP_SITE / ZULIP_BOT_EMAIL "
                        "/ ZULIP_BOT_API_KEY missing)."
                    )
                self._client = zulip.Client(
                    email=cfg.bot_email,
                    api_key=cfg.bot_api_key,
                    site=cfg.site,
                )
            return self._client

    def get_messages_in_topic(self, stream: str, topic: str, limit: int) -> List[Dict[str, Any]]:
        """Return the most recent `limit` messages in `stream`/`topic`, oldest first."""
        sdk = self._get_sdk()
        request = {
            "anchor": "newest",
            "num_before": limit,
            "num_after": 0,
            "narrow": [
                {"operator": "stream", "operand": stream},
                {"operator": "topic", "operand": topic},
            ],
            "apply_markdown": True,
        }
        result = sdk.get_messages(request)
        if result.get("result") != "success":
            raise ZulipClientError(f"Zulip get_messages failed: {result.get('msg', result)}")
        return result.get("messages", [])

    def send_message(self, stream: str, topic: str, content: str) -> int:
        """Post a message to `stream`/`topic`. Returns the new message id."""
        sdk = self._get_sdk()
        result = sdk.send_message(
            {
                "type": "stream",
                "to": stream,
                "topic": topic,
                "content": content,
            }
        )
        if result.get("result") != "success":
            raise ZulipClientError(f"Zulip send_message failed: {result.get('msg', result)}")
        return int(result["id"])


_default_client: Optional[ZulipClient] = None


def get_client() -> ZulipClient:
    """Return the process-wide default `ZulipClient`."""
    global _default_client
    if _default_client is None:
        _default_client = ZulipClient()
    return _default_client


def reset_client() -> None:
    """Drop the cached default client (used by tests)."""
    global _default_client
    _default_client = None
