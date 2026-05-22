"""Unit tests for ZulipConfigManager env-var handling."""

import pytest

from production_control.config.zulip_config import ZulipConfig, ZulipConfigManager


@pytest.fixture(autouse=True)
def clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in (
        "ZULIP_SITE",
        "ZULIP_BOT_EMAIL",
        "ZULIP_BOT_API_KEY",
        "ZULIP_STREAM",
        "ZULIP_TIMEOUT",
        "ZULIP_HISTORY_LIMIT",
    ):
        monkeypatch.delenv(var, raising=False)


def test_defaults() -> None:
    cfg = ZulipConfigManager().load_config()
    assert cfg.stream == "teelt"
    assert cfg.request_timeout == 5
    assert cfg.message_history_limit == 50
    assert cfg.site == ""
    assert cfg.bot_email == ""
    assert cfg.bot_api_key == ""


def test_env_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ZULIP_SITE", "https://zulip.example.com")
    monkeypatch.setenv("ZULIP_BOT_EMAIL", "bot@example.com")
    monkeypatch.setenv("ZULIP_BOT_API_KEY", "abc")
    monkeypatch.setenv("ZULIP_STREAM", "other-stream")
    monkeypatch.setenv("ZULIP_TIMEOUT", "12")
    monkeypatch.setenv("ZULIP_HISTORY_LIMIT", "7")

    cfg = ZulipConfigManager().load_config()

    assert cfg.site == "https://zulip.example.com"
    assert cfg.bot_email == "bot@example.com"
    assert cfg.bot_api_key == "abc"
    assert cfg.stream == "other-stream"
    assert cfg.request_timeout == 12
    assert cfg.message_history_limit == 7


def test_is_configured_requires_credentials() -> None:
    mgr = ZulipConfigManager()
    assert mgr.is_configured(ZulipConfig()) is False
    assert mgr.is_configured(ZulipConfig(site="x", bot_email="b", bot_api_key="k")) is True
