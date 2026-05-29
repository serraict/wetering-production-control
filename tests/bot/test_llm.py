"""Tests for bot.llm — model env config + MODEL_EXAMPLES."""

from __future__ import annotations

from production_control.bot import llm


def test_model_name_defaults_when_env_unset(monkeypatch):
    monkeypatch.delenv("BOT_MODEL", raising=False)
    assert llm.model_name() == llm.DEFAULT_MODEL


def test_model_name_honours_env(monkeypatch):
    monkeypatch.setenv("BOT_MODEL", "deepseek/deepseek-r1")
    assert llm.model_name() == "deepseek/deepseek-r1"


def test_model_examples_groups_present():
    """All four providers the user asked for must appear."""
    groups = set(llm.MODEL_EXAMPLES.keys())
    for needle in ("Claude", "Gemini", "Mistral", "DeepSeek"):
        assert any(needle in g for g in groups), f"missing provider group: {needle}"


def test_model_examples_default_is_listed():
    """The DEFAULT_MODEL identifier must appear under the Claude group."""
    flat = [slug for entries in llm.MODEL_EXAMPLES.values() for slug, _ in entries]
    assert llm.DEFAULT_MODEL in flat


def test_model_examples_entries_are_pairs_of_strings():
    for group, entries in llm.MODEL_EXAMPLES.items():
        assert entries, f"empty group: {group}"
        for entry in entries:
            assert isinstance(entry, tuple) and len(entry) == 2
            slug, note = entry
            assert isinstance(slug, str) and "/" in slug, f"bad slug: {slug!r}"
            assert isinstance(note, str) and note


class TestSystemMessage:
    """Anthropic prompt caching via OpenRouter — see
    https://openrouter.ai/docs/guides/best-practices/prompt-caching.

    Anthropic requires an explicit `cache_control` marker; other
    providers either auto-cache or do not yet support it via
    OpenRouter, so we only attach the marker for `anthropic/*` slugs.
    """

    def test_anthropic_default_wraps_content_with_cache_control(self, monkeypatch):
        monkeypatch.delenv("BOT_MODEL", raising=False)  # default = anthropic
        msg = llm.system_message("you are a bot")
        assert msg["role"] == "system"
        assert isinstance(msg["content"], list)
        assert msg["content"][0]["type"] == "text"
        assert msg["content"][0]["text"] == "you are a bot"
        assert msg["content"][0]["cache_control"] == {"type": "ephemeral"}

    def test_non_anthropic_model_returns_plain_string_content(self, monkeypatch):
        monkeypatch.setenv("BOT_MODEL", "deepseek/deepseek-r1")
        msg = llm.system_message("you are a bot")
        assert msg == {"role": "system", "content": "you are a bot"}

    def test_explicit_model_override_takes_precedence(self, monkeypatch):
        monkeypatch.setenv("BOT_MODEL", "deepseek/deepseek-r1")
        msg = llm.system_message("hi", model="anthropic/claude-haiku-4-5")
        assert isinstance(msg["content"], list)
        assert msg["content"][0]["cache_control"] == {"type": "ephemeral"}

    def test_supports_anthropic_caching_helper(self, monkeypatch):
        monkeypatch.setenv("BOT_MODEL", "anthropic/claude-sonnet-4.6")
        assert llm.supports_anthropic_caching() is True
        monkeypatch.setenv("BOT_MODEL", "google/gemini-2.5-pro")
        assert llm.supports_anthropic_caching() is False
        assert llm.supports_anthropic_caching("anthropic/claude-haiku-4-5") is True
