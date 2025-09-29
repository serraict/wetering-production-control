"""Tests for inspectie web page."""

from production_control.web.pages.inspectie import router, create_afwijking_actions


def test_inspectie_page_router_exists():
    """Test that inspectie page router exists."""
    assert router is not None


def test_create_afwijking_actions_exists():
    """Test that afwijking actions function exists."""
    actions = create_afwijking_actions()
    assert actions is not None
    assert "plus_one" in actions
    assert "minus_one" in actions
