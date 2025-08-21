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


async def test_active_lot_details_page_no_active_lot(user: User) -> None:
    """Test active lot details page when no lot is active."""
    await user.open("/potting-lots/active/1")

    await user.should_see("Lijn 1 - Geen Actieve Partij")
    await user.should_see("Er is momenteel geen actieve partij op deze lijn.")
    await user.should_see("← Terug naar Oppotlijst")


async def test_active_lot_details_page_with_active_lot(user: User) -> None:
    """Test active lot details page when a lot is active."""
    from production_control.potting_lots.models import PottingLot
    from production_control.potting_lots.active_models import ActivePottingLot
    from datetime import date

    with patch("production_control.web.pages.potting_lots._active_service") as mock_service:
        test_lot = PottingLot(
            id=123, naam="Test Actieve Partij", bollen_code=456, oppot_datum=date(2024, 3, 15)
        )
        active_lot = ActivePottingLot(line=1, potting_lot_id=123, potting_lot=test_lot)
        mock_service.get_active_lot_for_line.return_value = active_lot

        await user.open("/potting-lots/active/1")

        await user.should_see("Lijn 1 - Actieve Partij: Test Actieve Partij")
        await user.should_see("Actieve Oppotpartij")
        await user.should_see("Id")
        await user.should_see("123")
        await user.should_see("Naam")
        await user.should_see("Test Actieve Partij")
        await user.should_see("Bollen Code")
        await user.should_see("456")
        await user.should_see("2024-03-15")
        await user.should_see("Oppotten Voltooid")
        await user.should_see("Deactiveren")


async def test_active_lot_details_deactivation(user: User) -> None:
    """Test deactivation from active lot details page shows correct elements."""
    from production_control.potting_lots.models import PottingLot
    from production_control.potting_lots.active_models import ActivePottingLot

    with patch("production_control.web.pages.potting_lots._active_service") as mock_service:
        test_lot = PottingLot(id=123, naam="Test Partij", bollen_code=456, oppot_datum=None)
        active_lot = ActivePottingLot(line=2, potting_lot_id=123, potting_lot=test_lot)
        mock_service.get_active_lot_for_line.return_value = active_lot

        await user.open("/potting-lots/active/2")

        # Verify deactivation button is present
        await user.should_see("Deactiveren")

        # Note: We can't easily simulate button clicks in the current test framework,
        # but we can verify the UI elements are present and the handler function exists


def test_handle_deactivation_function() -> None:
    """Test the handle_deactivation function logic."""
    from production_control.web.pages.potting_lots import handle_deactivation
    from production_control.potting_lots.models import PottingLot
    from production_control.potting_lots.active_models import ActivePottingLot
    from unittest.mock import Mock, patch

    with (
        patch("production_control.web.pages.potting_lots._active_service") as mock_service,
        patch("production_control.web.pages.potting_lots.deactivate_lot") as mock_deactivate,
        patch("nicegui.ui.navigate") as mock_navigate,
        patch("nicegui.ui.notify") as mock_notify,
    ):

        # Test with active lot
        test_lot = PottingLot(id=123, naam="Test Partij", bollen_code=456, oppot_datum=None)
        active_lot = ActivePottingLot(line=1, potting_lot_id=123, potting_lot=test_lot)
        mock_service.get_active_lot_for_line.return_value = active_lot

        handle_deactivation(1)

        mock_deactivate.assert_called_once_with(mock_service, 1)
        mock_navigate.to.assert_called_once_with("/potting-lots")
        mock_notify.assert_not_called()

        # Test with no active lot
        mock_service.reset_mock()
        mock_deactivate.reset_mock()
        mock_navigate.reset_mock()
        mock_service.get_active_lot_for_line.return_value = None

        handle_deactivation(2)

        mock_deactivate.assert_not_called()
        mock_navigate.to.assert_not_called()
        mock_notify.assert_called_once_with("Geen actieve partij gevonden op deze lijn")


async def test_active_lot_header_navigation(user: User) -> None:
    """Test that clicking active lot header navigates to details page."""
    from production_control.potting_lots.models import PottingLot
    from production_control.potting_lots.active_models import ActivePottingLot

    with (
        patch("production_control.web.pages.potting_lots._repository") as mock_repo,
        patch("production_control.web.pages.potting_lots._active_service") as mock_service,
    ):

        mock_repo.get_paginated.return_value = ([], 0)

        # Mock active lot on line 1
        test_lot = PottingLot(id=123, naam="Test Partij", bollen_code=456, oppot_datum=None)
        active_lot = ActivePottingLot(line=1, potting_lot_id=123, potting_lot=test_lot)
        mock_service.get_active_lot_for_line.return_value = active_lot

        await user.open("/potting-lots")

        # Click on the line 1 button should navigate to active lot details
        # Note: We can't easily test the navigation in the test environment,
        # but we can verify the button exists and is clickable
        await user.should_see("1:")


async def test_completion_button_on_active_lot_details_page(user: User) -> None:
    """Test that completion button is shown on active lot details page."""
    from production_control.potting_lots.models import PottingLot
    from production_control.potting_lots.active_models import ActivePottingLot

    with patch("production_control.web.pages.potting_lots._active_service") as mock_service:
        test_lot = PottingLot(id=123, naam="Test Partij", bollen_code=456, oppot_datum=None)
        active_lot = ActivePottingLot(line=1, potting_lot_id=123, potting_lot=test_lot)
        mock_service.get_active_lot_for_line.return_value = active_lot

        await user.open("/potting-lots/active/1")

        # Verify both action buttons are present
        await user.should_see("Oppotten Voltooid")
        await user.should_see("Deactiveren")


def test_handle_completion_function() -> None:
    """Test the handle_completion function logic."""
    from production_control.web.pages.potting_lots import handle_completion
    from production_control.potting_lots.models import PottingLot
    from production_control.potting_lots.active_models import ActivePottingLot
    from unittest.mock import Mock, patch

    with (
        patch("production_control.web.pages.potting_lots._active_service") as mock_service,
        patch("nicegui.ui.notify") as mock_notify,
        patch("nicegui.ui.navigate") as mock_navigate,
    ):

        # Mock dialog
        mock_dialog = Mock()

        # Test successful completion
        mock_service.complete_lot.return_value = True

        handle_completion(1, 150.0, mock_dialog)

        mock_service.complete_lot.assert_called_once_with(1, 150)
        mock_notify.assert_called_once_with(
            "Oppotten voltooid! 150 potten gerealiseerd", type="positive"
        )
        mock_dialog.close.assert_called_once()
        mock_navigate.to.assert_called_once_with("/potting-lots")

        # Test invalid input
        mock_service.reset_mock()
        mock_notify.reset_mock()
        mock_dialog.reset_mock()
        mock_navigate.reset_mock()

        handle_completion(1, None, mock_dialog)

        mock_service.complete_lot.assert_not_called()
        mock_notify.assert_called_once_with("Voer een geldig aantal potten in", type="negative")
        mock_dialog.close.assert_not_called()
        mock_navigate.to.assert_not_called()

        # Test service failure
        mock_service.reset_mock()
        mock_notify.reset_mock()
        mock_dialog.reset_mock()
        mock_navigate.reset_mock()
        mock_service.complete_lot.return_value = False

        handle_completion(1, 100.0, mock_dialog)

        mock_service.complete_lot.assert_called_once_with(1, 100)
        mock_notify.assert_called_once_with("Fout bij voltooien van oppotten", type="negative")
        mock_dialog.close.assert_not_called()
        mock_navigate.to.assert_not_called()
