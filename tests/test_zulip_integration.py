"""Integration tests for the Zulip chat backend.

Run with `uv run pytest -m integration tests/test_zulip_integration.py`.

Requires a reachable Zulip server with bot credentials supplied via the
`ZULIP_SITE`, `ZULIP_BOT_EMAIL`, `ZULIP_BOT_API_KEY` env vars and a stream the
bot can post to (defaults to `teelt`, override with `ZULIP_STREAM`). Tests use
a random topic so they don't interfere with real conversations.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass

import pytest

from production_control.config.zulip_config import ZulipConfigManager
from production_control.zulip_chat import service as zulip_service
from production_control.zulip_chat.client import ZulipClient

pytestmark = pytest.mark.integration


@dataclass
class FakeLot:
    id: int


@pytest.fixture
def configured_client() -> ZulipClient:
    mgr = ZulipConfigManager()
    cfg = mgr.load_config()
    if not mgr.is_configured(cfg):
        pytest.skip("Zulip env vars not set; skipping integration test")
    return ZulipClient(config=cfg)


@pytest.fixture
def throwaway_lot() -> FakeLot:
    # Random high id so the topic name is unique per run.
    lot_id = int(uuid.uuid4().int % 10_000_000) + 9_000_000_000
    return FakeLot(id=lot_id)


def test_post_and_read_back(configured_client: ZulipClient, throwaway_lot: FakeLot) -> None:
    cfg = ZulipConfigManager().load_config()
    body = f"integration-test {uuid.uuid4()}"

    msg_id = zulip_service.post(
        throwaway_lot,
        body,
        user_name="pytest",
        client=configured_client,
        config=cfg,
    )
    assert msg_id > 0

    messages = zulip_service.get_messages(
        throwaway_lot, client=configured_client, config=cfg
    )
    assert messages, "expected at least one message in the freshly created topic"
    assert any(body in m.content_html for m in messages)
    assert any("pytest" in m.content_html for m in messages)


def test_get_messages_for_empty_topic_returns_empty_list(
    configured_client: ZulipClient,
) -> None:
    cfg = ZulipConfigManager().load_config()
    # A topic ID that is essentially guaranteed not to exist.
    lot = FakeLot(id=int(uuid.uuid4().int % 10**12) + 10**12)
    messages = zulip_service.get_messages(lot, client=configured_client, config=cfg)
    assert messages == []


def test_narrow_url_uses_configured_site() -> None:
    cfg = ZulipConfigManager().load_config()
    if not cfg.site:
        pytest.skip("ZULIP_SITE not set")
    url = zulip_service.narrow_url(FakeLot(id=1), config=cfg)
    assert url.startswith(cfg.site.rstrip("/"))
    assert "/narrow/stream/" in url
    assert url.endswith("/topic/1")
