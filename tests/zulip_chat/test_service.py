"""Unit tests for zulip_chat.service with the client mocked."""

from dataclasses import dataclass
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from production_control.config.zulip_config import ZulipConfig
from production_control.zulip_chat import service as zulip_service
from production_control.zulip_chat.client import ZulipClientError
from production_control.zulip_chat.service import ZulipServiceError


@dataclass
class FakeLot:
    id: int = 42


@pytest.fixture
def config() -> ZulipConfig:
    return ZulipConfig(
        site="https://zulip.test",
        bot_email="bot@zulip.test",
        bot_api_key="secret",
        stream="teelt",
        message_history_limit=10,
    )


def test_get_messages_returns_dataclasses(config: ZulipConfig) -> None:
    client = MagicMock()
    client.get_messages_in_topic.return_value = [
        {
            "id": 1,
            "sender_full_name": "production-bot",
            "timestamp": 1_700_000_000,
            "content": "<p><strong>Marijn</strong>: hallo</p>",
        }
    ]

    messages = zulip_service.get_messages(FakeLot(), client=client, config=config)

    client.get_messages_in_topic.assert_called_once_with("teelt", "42", 10)
    assert len(messages) == 1
    msg = messages[0]
    assert msg.id == 1
    assert msg.sender_full_name == "production-bot"
    assert msg.content_html == "<p><strong>Marijn</strong>: hallo</p>"
    assert msg.author_name == "Marijn"
    assert msg.body_html == "<p>hallo</p>"
    assert msg.timestamp == datetime.fromtimestamp(1_700_000_000, tz=timezone.utc)


def test_get_messages_falls_back_when_no_prefix(config: ZulipConfig) -> None:
    client = MagicMock()
    client.get_messages_in_topic.return_value = [
        {
            "id": 2,
            "sender_full_name": "production-bot",
            "timestamp": 1_700_000_000,
            "content": "<p>plain message</p>",
        }
    ]
    msg = zulip_service.get_messages(FakeLot(), client=client, config=config)[0]
    assert msg.author_name == "production-bot"
    assert msg.body_html == "<p>plain message</p>"


def test_get_messages_empty(config: ZulipConfig) -> None:
    client = MagicMock()
    client.get_messages_in_topic.return_value = []
    assert zulip_service.get_messages(FakeLot(), client=client, config=config) == []


def test_get_messages_wraps_client_error(config: ZulipConfig) -> None:
    client = MagicMock()
    client.get_messages_in_topic.side_effect = ZulipClientError("boom")
    with pytest.raises(ZulipServiceError, match="boom"):
        zulip_service.get_messages(FakeLot(), client=client, config=config)


def test_post_prefixes_user_name(config: ZulipConfig) -> None:
    client = MagicMock()
    client.send_message.return_value = 99

    msg_id = zulip_service.post(
        FakeLot(),
        "hallo wereld",
        user_name="Marijn",
        client=client,
        config=config,
    )

    assert msg_id == 99
    client.send_message.assert_called_once_with(
        "teelt", "42", "**Marijn**: hallo wereld"
    )


def test_post_uses_guest_by_default(config: ZulipConfig) -> None:
    client = MagicMock()
    client.send_message.return_value = 1
    zulip_service.post(FakeLot(), "hi", client=client, config=config)
    args, _ = client.send_message.call_args
    assert args[2].startswith("**Guest**: ")


def test_post_rejects_empty(config: ZulipConfig) -> None:
    client = MagicMock()
    with pytest.raises(ZulipServiceError):
        zulip_service.post(FakeLot(), "   ", client=client, config=config)
    client.send_message.assert_not_called()


def test_post_wraps_client_error(config: ZulipConfig) -> None:
    client = MagicMock()
    client.send_message.side_effect = ZulipClientError("denied")
    with pytest.raises(ZulipServiceError, match="denied"):
        zulip_service.post(FakeLot(), "hi", client=client, config=config)


def test_narrow_url(config: ZulipConfig) -> None:
    url = zulip_service.narrow_url(FakeLot(id=42), config=config)
    assert url == "https://zulip.test/#narrow/stream/teelt/topic/42"


def test_narrow_url_blank_when_site_missing() -> None:
    cfg = ZulipConfig(site="", bot_email="x", bot_api_key="y")
    assert zulip_service.narrow_url(FakeLot(), config=cfg) == ""
