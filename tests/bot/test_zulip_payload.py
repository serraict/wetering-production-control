"""Tests for the Zulip webhook payload models + mention stripping."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from production_control.bot.zulip_payload import (
    ZulipWebhookPayload,
    strip_mention,
)


class TestPayload:
    def test_minimal_required_fields(self):
        p = ZulipWebhookPayload(token="t", bot_full_name="Bot", data="hi")
        assert p.token == "t"
        assert p.bot_full_name == "Bot"
        assert p.data == "hi"
        assert p.message is None

    def test_extra_fields_ignored(self):
        p = ZulipWebhookPayload(
            token="t",
            bot_full_name="Bot",
            data="hi",
            trigger="mention",
            bot_email="bot@org",
            random_zulip_field="something",
        )
        assert p.token == "t"
        assert not hasattr(p, "trigger")

    def test_nested_message_type(self):
        p = ZulipWebhookPayload(
            token="t",
            bot_full_name="Bot",
            data="hi",
            message={"type": "private", "id": 5, "sender_email": "a@b"},
        )
        assert p.message is not None
        assert p.message.type == "private"

    def test_missing_required_field_raises(self):
        with pytest.raises(ValidationError):
            ZulipWebhookPayload(bot_full_name="Bot", data="hi")  # type: ignore[call-arg]


class TestStripMention:
    BOT = "Insights Bot"

    def test_strips_standard_mention(self):
        assert strip_mention("@**Insights Bot** hoi", self.BOT) == "hoi"

    def test_strips_silent_mention(self):
        assert strip_mention("@_**Insights Bot** hoi", self.BOT) == "hoi"

    def test_strips_leading_whitespace_then_mention(self):
        assert strip_mention("   @**Insights Bot**   hoi   ", self.BOT) == "hoi"

    def test_no_mention_returns_trimmed_input(self):
        """DM case: no mention, just message text."""
        assert strip_mention("  wat speelt er  ", self.BOT) == "wat speelt er"

    def test_empty_after_stripping(self):
        assert strip_mention("@**Insights Bot**", self.BOT) == ""

    def test_only_strips_at_start(self):
        """A mention in the middle is left alone (very atypical)."""
        s = "hoi @**Insights Bot** wat"
        assert strip_mention(s, self.BOT) == s

    def test_only_strips_one_mention(self):
        """Two leading mentions: only the first is stripped."""
        s = "@**Insights Bot** @**Insights Bot** hoi"
        out = strip_mention(s, self.BOT)
        assert out == "@**Insights Bot** hoi"

    def test_bot_name_with_spaces(self):
        assert strip_mention("@**Wetering Insights Bot** vraag", "Wetering Insights Bot") == "vraag"

    def test_different_bot_name_not_stripped(self):
        assert strip_mention("@**Other Bot** hoi", "Insights Bot") == "@**Other Bot** hoi"
