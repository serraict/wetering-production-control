"""Tests for spacing web interface."""

from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch
from uuid import UUID

from nicegui.testing import User
from nicegui import ui

from production_control.spacing.models import WijderzetRegistratie


async def test_spacing_page_exists(user: User) -> None:
    """Test that spacing page exists and shows header."""
    # When
    await user.open("/spacing")

    # Then
    await user.should_see("Wijderzetten Overzicht")


async def test_spacing_page_shows_table_structure(user: User) -> None:
    """Test that spacing page shows a table with correct columns."""
    with patch("production_control.web.pages.spacing.SpacingRepository") as mock_repo_class:
        # Given
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_paginated.return_value = ([], 0)  # Empty result for now

        # When
        await user.open("/spacing")

        # Then
        table = user.find(ui.table).elements.pop()
        assert table.columns == [
            {
                "name": "partij_code",
                "label": "Partij Code",
                "field": "partij_code",
                "sortable": True,
            },
            {
                "name": "product_naam",
                "label": "Product",
                "field": "product_naam",
                "sortable": True,
            },
            {
                "name": "productgroep_naam",
                "label": "Productgroep",
                "field": "productgroep_naam",
                "sortable": True,
            },
            {
                "name": "aantal_tafels_totaal",
                "label": "Totaal Tafels",
                "field": "aantal_tafels_totaal",
                "sortable": True,
            },
            {
                "name": "wijderzet_registratie_fout",
                "label": "Heeft Fout",
                "field": "wijderzet_registratie_fout",
            },
            {"name": "actions", "label": "Acties", "field": "actions"},
        ]


async def test_spacing_page_loads_data(user: User) -> None:
    """Test that spacing page loads and displays data."""
    with patch("production_control.web.pages.spacing.SpacingRepository") as mock_repo_class:
        # Given
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        test_date = date(2023, 1, 1)
        test_records = [
            WijderzetRegistratie(
                id=UUID("12345678-1234-5678-1234-567812345678"),
                partij_code="TEST123",
                product_naam="Test Plant",
                productgroep_naam="Test Group",
                datum_oppotten_real=test_date,
                datum_uit_cel_real=test_date,
                datum_wdz1_real=test_date,
                datum_wdz2_real=test_date,
                aantal_planten_gerealiseerd=100,
                aantal_tafels_totaal=10,
                aantal_tafels_na_wdz1=15,
                aantal_tafels_na_wdz2=20,
                aantal_tafels_oppotten_plan=Decimal("10.0"),
                dichtheid_oppotten_plan=100,
                dichtheid_wz1_plan=50,
                dichtheid_wz2_plan=25.0,
                wijderzet_registratie_fout=False,
            ),
        ]
        mock_repo.get_paginated.return_value = (test_records, 1)

        # When
        await user.open("/spacing")

        # Then
        # Verify repository was called
        mock_repo.get_paginated.assert_called_once()

        # Verify data is displayed
        table = user.find(ui.table).elements.pop()
        assert table.rows == [
            {
                "id": "12345678-1234-5678-1234-567812345678",
                "partij_code": "TEST123",
                "product_naam": "Test Plant",
                "productgroep_naam": "Test Group",
                "aantal_tafels_totaal": 10,
                "wijderzet_registratie_fout": False,
            },
        ]
