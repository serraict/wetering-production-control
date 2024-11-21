"""Tests for spacing record editing functionality."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock

from nicegui import ui
from nicegui.testing import User

from production_control.spacing.models import WijderzetRegistratie
from production_control.spacing.commands import CorrectSpacingRecord


async def test_spacing_correction_page_shows_fields(user: User) -> None:
    """Test that correction page shows correct fields and values."""
    with patch("production_control.web.pages.spacing.SpacingRepository") as mock_repo_class:
        # Given
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        test_date = date(2023, 1, 1)  # This is week 52 of 2022, day 7 (Sunday)
        test_record = WijderzetRegistratie(
            partij_code="TEST123",
            product_naam="Test Plant",
            productgroep_naam="Test Group",
            aantal_tafels_totaal=10,
            aantal_tafels_na_wdz1=15,
            aantal_tafels_na_wdz2=20,
            aantal_tafels_oppotten_plan=Decimal("10.0"),
            aantal_planten_gerealiseerd=100,
            datum_wdz1_real=test_date,
            datum_wdz2_real=test_date,
            datum_oppotten_real=test_date,
            datum_uit_cel_real=test_date,
            dichtheid_oppotten_plan=100,
            dichtheid_wz1_plan=50,
            dichtheid_wz2_plan=25.0,
            wijderzet_registratie_fout="Test error message",
        )
        mock_repo.get_by_id.return_value = test_record

        # When
        await user.open("/spacing/correct/TEST123")

        # Then
        # Verify page title and record info
        await user.should_see("Wijderzet Correctie")
        await user.should_see("TEST123 - Test Plant")
        await user.should_see("de productgroep: Test Group")
        await user.should_see("oppotten: 22w52-7")
        await user.should_see("gerealiseerde planten: 100")
        await user.should_see("tafels volgens oppot plan: 10.0")

        # Verify error message is shown
        await user.should_see("Fout")
        await user.should_see("Test error message")

        # Verify input fields and dates exist
        await user.should_see("tafels na wijderzet 1")
        await user.should_see("wijderzet 1: 22w52-7")
        await user.should_see("tafels na wijderzet 2")
        await user.should_see("wijderzet 2: 22w52-7")

        # Verify buttons exist
        await user.should_see("Opslaan")
        await user.should_see("Annuleren")


async def test_spacing_correction_page_saves_changes(user: User) -> None:
    """Test that correction page saves changes through OpTechClient."""
    with (
        patch("production_control.web.pages.spacing.SpacingRepository") as mock_repo_class,
        patch("production_control.web.pages.spacing.OpTechClient") as mock_client_class,
    ):
        # Given
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        test_record = WijderzetRegistratie(
            partij_code="TEST123",
            product_naam="Test Plant",
            productgroep_naam="Test Group",
            aantal_tafels_totaal=10,
            aantal_tafels_na_wdz1=15,
            aantal_tafels_na_wdz2=20,
            aantal_tafels_oppotten_plan=Decimal("10.0"),
            aantal_planten_gerealiseerd=100,
            datum_wdz1_real=date(2023, 1, 1),
            datum_wdz2_real=date(2023, 1, 1),
            datum_oppotten_real=date(2023, 1, 1),
            datum_uit_cel_real=date(2023, 1, 1),
            dichtheid_oppotten_plan=100,
            dichtheid_wz1_plan=50,
            dichtheid_wz2_plan=25.0,
            wijderzet_registratie_fout=None,
        )
        mock_repo.get_by_id.return_value = test_record

        # When
        await user.open("/spacing/correct/TEST123")
        save_button = user.find(kind=ui.button, content="Opslaan")
        save_button.click()

        # Then
        mock_client.send_correction.assert_called_once()
        command = mock_client.send_correction.call_args[0][0]
        assert isinstance(command, CorrectSpacingRecord)
        assert command.partij_code == "TEST123"
        assert command.aantal_tafels_na_wdz1 == 15
        assert command.aantal_tafels_na_wdz2 == 20
