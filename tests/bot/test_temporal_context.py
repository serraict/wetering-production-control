"""Tests for the temporal context block in the bot's system prompt."""

from __future__ import annotations

from datetime import date, datetime, timezone

from production_control.bot.answer import _temporal_context


THURSDAY = date(2026, 5, 28)  # ISO: 2026-W22-4


def test_iso_week_date_form():
    out = _temporal_context(THURSDAY)
    assert "2026-W22-4" in out


def test_iso_calendar_date_form():
    out = _temporal_context(THURSDAY)
    assert "2026-05-28" in out


def test_weekday_name():
    out = _temporal_context(THURSDAY)
    assert "Thursday" in out


def test_gregorian_year():
    out = _temporal_context(THURSDAY)
    assert "Current year: 2026" in out


def test_week_bounds_are_monday_to_sunday():
    out = _temporal_context(THURSDAY)
    assert "2026-W22-1" in out
    assert "2026-05-25" in out  # Monday
    assert "2026-W22-7" in out
    assert "2026-05-31" in out  # Sunday


def test_deterministic_given_same_input():
    assert _temporal_context(THURSDAY) == _temporal_context(THURSDAY)


def test_accepts_datetime_and_normalizes_to_date():
    """A datetime (even with a tz) should produce the same block as its date."""
    dt = datetime(2026, 5, 28, 14, 30, tzinfo=timezone.utc)
    assert _temporal_context(dt) == _temporal_context(THURSDAY)


def test_iso_year_boundary_uses_iso_year_for_week_label():
    """2025-12-29 is Monday of 2026-W01 — week label should use the ISO year."""
    monday = date(2025, 12, 29)
    out = _temporal_context(monday)
    assert "2026-W01-1" in out  # ISO year for the week label
    assert "Current year: 2025" in out  # Gregorian year for "current year"


def test_block_header_is_current_date():
    out = _temporal_context(THURSDAY)
    assert out.lstrip().startswith("## Current date")
