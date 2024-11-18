"""Tests for spacing web interface."""

from unittest.mock import Mock, patch
from nicegui.testing import User
from nicegui import ui


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
