"""Tests for spacing record editing functionality."""

from datetime import date
from decimal import Decimal
from unittest.mock import patch, MagicMock

from nicegui.testing import User

from production_control.spacing.models import WijderzetRegistratie


async def test_spacing_correction_page_shows_fields(user: User) -> None:
    """Test that correction page shows correct fields and values."""
    with patch("production_control.web.pages.spacing.SpacingRepository") as mock_repo_class:
        # Given
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        test_date = date(2023, 1, 1)
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
            wijderzet_registratie_fout=False,
        )
        mock_repo.get_by_id.return_value = test_record

        # When
        await user.open("/spacing/correct/TEST123")

        # Then
        # Verify page title and record info
        await user.should_see("Wijderzet Correctie")
        await user.should_see("Partij: TEST123")
        await user.should_see("Product: Test Plant")

        # Verify labels for input fields
        await user.should_see("Tafels na WZ1")
        await user.should_see("Tafels na WZ2")

        # Verify buttons exist
        await user.should_see("Opslaan")
        await user.should_see("Annuleren")
