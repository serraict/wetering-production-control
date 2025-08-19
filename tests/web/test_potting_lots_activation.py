"""Tests for potting lots activation functionality."""

from unittest.mock import patch
from nicegui.testing import User
from production_control.potting_lots.models import PottingLot


async def test_activation_ui_shows_available_lines(user: User) -> None:
    """Test that activation UI shows available lines for activation."""
    with patch("production_control.web.pages.potting_lots._repository") as mock_repo:
        test_lot = PottingLot(id=1, naam="Test Partij", bollen_code=123, oppot_datum=None)
        mock_repo.get_by_id.return_value = test_lot

        await user.open("/potting-lots/1")

        await user.should_see("Terug naar Oppotlijst")
        await user.should_see("Activeren op Lijn 1")
        await user.should_see("Activeren op Lijn 2")


async def test_activation_ui_shows_active_status(user: User) -> None:
    """Test that activation UI shows when a lot is active."""
    with patch("production_control.web.pages.potting_lots._repository") as mock_repo:
        test_lot = PottingLot(id=1, naam="Test Partij", bollen_code=123, oppot_datum=None)

        mock_repo.get_by_id.return_value = test_lot

        await user.open("/potting-lots/1")
        await user.should_see("Activeren op Lijn 2")


async def test_potting_lots_page_shows_active_header(user: User) -> None:
    """Test that the potting lots main page shows active lots header."""
    with patch("production_control.web.pages.potting_lots._repository") as mock_repo:
        mock_repo.get_paginated.return_value = ([], 0)  # Return empty list for the table

        await user.open("/potting-lots")

        # buttons for the potting lines
        await user.should_see("1:")
        await user.should_see("2:")
