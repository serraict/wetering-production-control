"""Tests for the in-process conversation store."""

from __future__ import annotations

import pytest

from production_control.bot import conversation


@pytest.fixture(autouse=True)
def _clean():
    conversation.clear_all()
    yield
    conversation.clear_all()


def _msg(role: str, content: str) -> dict:
    return {"role": role, "content": content}


class TestRecall:
    def test_unknown_key_returns_empty(self):
        assert conversation.recall("nope") == []

    def test_after_extend_returns_messages(self):
        conversation.extend("k", [_msg("user", "hi"), _msg("assistant", "hoi")], 10)
        assert conversation.recall("k") == [
            _msg("user", "hi"),
            _msg("assistant", "hoi"),
        ]

    def test_keys_are_isolated(self):
        conversation.extend("a", [_msg("user", "1")], 5)
        conversation.extend("b", [_msg("user", "2")], 5)
        assert conversation.recall("a") == [_msg("user", "1")]
        assert conversation.recall("b") == [_msg("user", "2")]


class TestReset:
    def test_reset_drops_history(self):
        conversation.extend("k", [_msg("user", "hi")], 5)
        conversation.reset("k")
        assert conversation.recall("k") == []

    def test_reset_unknown_key_is_noop(self):
        conversation.reset("never-seen")  # must not raise

    def test_reset_one_key_leaves_others(self):
        conversation.extend("a", [_msg("user", "1")], 5)
        conversation.extend("b", [_msg("user", "2")], 5)
        conversation.reset("a")
        assert conversation.recall("a") == []
        assert conversation.recall("b") == [_msg("user", "2")]


class TestExtend:
    def test_empty_messages_is_noop(self):
        conversation.extend("k", [], 0)
        assert conversation.recall("k") == []

    def test_turns_concatenate_in_order(self):
        conversation.extend("k", [_msg("user", "1"), _msg("assistant", "a1")], 5)
        conversation.extend("k", [_msg("user", "2"), _msg("assistant", "a2")], 5)
        assert conversation.recall("k") == [
            _msg("user", "1"),
            _msg("assistant", "a1"),
            _msg("user", "2"),
            _msg("assistant", "a2"),
        ]


class TestTurnCap:
    def test_oldest_turn_drops_when_turn_cap_exceeded(self, monkeypatch):
        monkeypatch.setenv("BOT_MAX_TURNS", "3")
        for i in range(5):
            conversation.extend("k", [_msg("user", f"q{i}")], 1)
        # Only the most recent 3 turns survive.
        assert conversation.recall("k") == [
            _msg("user", "q2"),
            _msg("user", "q3"),
            _msg("user", "q4"),
        ]

    def test_default_cap_keeps_recent_turns(self):
        # With default cap (8 turns), 10 small turns trim to last 8.
        for i in range(10):
            conversation.extend("k", [_msg("user", f"q{i}")], 1)
        history = conversation.recall("k")
        assert len(history) == 8
        assert history[0] == _msg("user", "q2")
        assert history[-1] == _msg("user", "q9")


class TestTokenCap:
    def test_oldest_turn_drops_when_token_cap_exceeded(self, monkeypatch):
        monkeypatch.setenv("BOT_MAX_HISTORY_TOKENS", "100")
        conversation.extend("k", [_msg("user", "1")], 60)
        conversation.extend("k", [_msg("user", "2")], 60)
        # Sum 120 > 100, so the oldest turn drops.
        assert conversation.recall("k") == [_msg("user", "2")]

    def test_token_cap_evicts_multiple_old_turns(self, monkeypatch):
        monkeypatch.setenv("BOT_MAX_HISTORY_TOKENS", "100")
        conversation.extend("k", [_msg("user", "a")], 40)
        conversation.extend("k", [_msg("user", "b")], 40)
        conversation.extend("k", [_msg("user", "c")], 40)
        conversation.extend("k", [_msg("user", "d")], 80)
        # After the last big turn, sum would be 200 → keep only "d" (80 ≤ 100).
        assert conversation.recall("k") == [_msg("user", "d")]

    def test_always_keeps_at_least_latest_turn(self, monkeypatch):
        monkeypatch.setenv("BOT_MAX_HISTORY_TOKENS", "10")
        conversation.extend("k", [_msg("user", "huge")], 9_999)
        # One turn alone over the cap: still retained.
        assert conversation.recall("k") == [_msg("user", "huge")]


class TestCapEnvFallback:
    def test_garbage_env_falls_back_to_default(self, monkeypatch):
        monkeypatch.setenv("BOT_MAX_TURNS", "not-a-number")
        for i in range(conversation.DEFAULT_MAX_TURNS + 2):
            conversation.extend("k", [_msg("user", f"q{i}")], 1)
        assert len(conversation.recall("k")) == conversation.DEFAULT_MAX_TURNS
