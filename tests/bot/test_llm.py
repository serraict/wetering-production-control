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
