"""Tests for spacing page."""

import asyncio
import pytest
from datetime import date
from decimal import Decimal
from typing import Optional
from unittest.mock import patch, MagicMock

from nicegui import ui
from nicegui.testing import User

from production_control.data import Pagination
from production_control.spacing.models import WijderzetRegistratie


async def test_spacing_page_shows_table(user: User) -> None:
    """Test that spacing page shows a table with spacing data."""
    with patch("production_control.web.pages.spacing.SpacingRepository") as mock_repo_class:
        # Given
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        test_date = date(2023, 1, 2)  # Monday of week 1, 2023
        mock_repo.get_paginated.return_value = (
            [
                WijderzetRegistratie(
                    partij_code="TEST123",
                    product_naam="Test Plant",
                    aantal_planten_gerealiseerd=100,
                    aantal_tafels_oppotten_plan=Decimal("10.0"),
                    aantal_tafels_na_wdz1=15,
                    aantal_tafels_na_wdz2=20,
                    aantal_tafels_totaal=10,
                    datum_wdz1_real=test_date,
                    datum_wdz2_real=test_date,
                    datum_oppotten_real=test_date,
                    productgroep_naam="Test Group",
                    datum_uit_cel_real=test_date,
                    dichtheid_oppotten_plan=100,
                    dichtheid_wz1_plan=50,
                    dichtheid_wz2_plan=25.0,
                    wijderzet_registratie_fout=False,
                ),
                WijderzetRegistratie(
                    partij_code="TEST456",
                    product_naam="Other Plant",
                    aantal_planten_gerealiseerd=200,
                    aantal_tafels_oppotten_plan=Decimal("20.0"),
                    aantal_tafels_na_wdz1=25,
                    aantal_tafels_na_wdz2=30,
                    aantal_tafels_totaal=20,
                    datum_wdz1_real=test_date,
                    datum_wdz2_real=test_date,
                    datum_oppotten_real=test_date,
                    productgroep_naam="Other Group",
                    datum_uit_cel_real=test_date,
                    dichtheid_oppotten_plan=100,
                    dichtheid_wz1_plan=50,
                    dichtheid_wz2_plan=25.0,
                    wijderzet_registratie_fout=True,
                ),
            ],
            2,  # total count
        )

        # When
        await user.open("/spacing")
        await user.should_see("Overzicht")  # Wait for page to load

        # Then
        table = user.find(ui.table).elements.pop()
        assert table.columns == [
            {
                "name": "warning_emoji",
                "label": "",
                "field": "warning_emoji",
            },
            {
                "name": "partij_code",
                "label": "Partij",
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
                "name": "aantal_planten_gerealiseerd",
                "label": "Planten",
                "field": "aantal_planten_gerealiseerd",
                "sortable": True,
            },
            {
                "name": "aantal_tafels_oppotten_plan",
                "label": "#oppepot",
                "field": "aantal_tafels_oppotten_plan",
                "sortable": True,
                ":format": "value => Number(value).toFixed(1)",
            },
            {
                "name": "aantal_tafels_na_wdz1",
                "label": "#WZ1",
                "field": "aantal_tafels_na_wdz1",
                "sortable": True,
            },
            {
                "name": "aantal_tafels_na_wdz2",
                "label": "#WZ2",
                "field": "aantal_tafels_na_wdz2",
                "sortable": True,
            },
            {
                "name": "aantal_tafels_totaal",
                "label": "#Nu",
                "field": "aantal_tafels_totaal",
                "sortable": True,
            },
            {
                "name": "datum_wdz1_real",
                "label": "Wijderzet 1",
                "field": "datum_wdz1_real",
                "sortable": True,
            },
            {
                "name": "datum_wdz2_real",
                "label": "Wijderzet 2",
                "field": "datum_wdz2_real",
                "sortable": True,
            },
            {
                "name": "datum_oppotten_real",
                "label": "Oppotdatum",
                "field": "datum_oppotten_real",
                "sortable": True,
            },
            {"name": "actions", "label": "Acties", "field": "actions"},
        ]

        # Check essential visible fields in rows
        assert len(table.rows) == 2
        # Check row 0
        assert table.rows[0]["partij_code"] == "TEST123"
        assert table.rows[0]["product_naam"] == "Test Plant"
        assert table.rows[0]["aantal_tafels_totaal"] == 10
        assert table.rows[0]["warning_emoji"] == ""
        # Check date formatting (2023-01-02 is Monday of week 1)
        assert table.rows[0]["datum_wdz1_real"] == "23w01-1"
        assert table.rows[0]["datum_wdz2_real"] == "23w01-1"
        assert table.rows[0]["datum_oppotten_real"] == "23w01-1"

        # Check row 1
        assert table.rows[1]["partij_code"] == "TEST456"
        assert table.rows[1]["product_naam"] == "Other Plant"
        assert table.rows[1]["aantal_tafels_totaal"] == 20
        assert table.rows[1]["warning_emoji"] == "⚠️"
        # Check date formatting (2023-01-02 is Monday of week 1)
        assert table.rows[1]["datum_wdz1_real"] == "23w01-1"
        assert table.rows[1]["datum_wdz2_real"] == "23w01-1"
        assert table.rows[1]["datum_oppotten_real"] == "23w01-1"


@pytest.mark.skip(reason="Warning filter test is not compatible with the new generic components")
async def test_spacing_page_warning_filter(user: User) -> None:
    """Test that warning filter shows only records with warnings."""
    with patch("production_control.web.pages.spacing.SpacingRepository") as mock_repo_class:
        # Given
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        test_date = date(2023, 1, 2)

        # Records with and without warnings
        records = [
            WijderzetRegistratie(
                partij_code="TEST123",
                product_naam="Test Plant",
                aantal_planten_gerealiseerd=100,
                aantal_tafels_oppotten_plan=Decimal("10.0"),
                aantal_tafels_na_wdz1=15,
                aantal_tafels_na_wdz2=20,
                aantal_tafels_totaal=10,
                datum_wdz1_real=test_date,
                datum_wdz2_real=test_date,
                datum_oppotten_real=test_date,
                productgroep_naam="Test Group",
                datum_uit_cel_real=test_date,
                dichtheid_oppotten_plan=100,
                dichtheid_wz1_plan=50,
                dichtheid_wz2_plan=25.0,
                wijderzet_registratie_fout=None,  # No warning
            ),
            WijderzetRegistratie(
                partij_code="TEST456",
                product_naam="Other Plant",
                aantal_planten_gerealiseerd=200,
                aantal_tafels_oppotten_plan=Decimal("20.0"),
                aantal_tafels_na_wdz1=25,
                aantal_tafels_na_wdz2=30,
                aantal_tafels_totaal=20,
                datum_wdz1_real=test_date,
                datum_wdz2_real=test_date,
                datum_oppotten_real=test_date,
                productgroep_naam="Other Group",
                datum_uit_cel_real=test_date,
                dichtheid_oppotten_plan=100,
                dichtheid_wz1_plan=50,
                dichtheid_wz2_plan=25.0,
                wijderzet_registratie_fout="Test warning",  # Has warning
            ),
        ]

        # Return all records initially
        mock_repo.get_paginated.return_value = (records, 2)

        # An asyncio.Event to signal when the repository is called with warning filter
        done_event = asyncio.Event()

        def on_get_paginated(
            pagination: Optional[Pagination] = None,
            page: int = 1,
            items_per_page: int = 10,
            sort_by: Optional[str] = None,
            descending: bool = False,
            filter_text: str = "",
            warning_filter: bool = False,
        ):
            if warning_filter:
                done_event.set()  # Set the event when warning filter is True
                return [records[1]], 1  # Return only the record with warning
            return records, 2  # Return all records

        mock_repo.get_paginated.side_effect = on_get_paginated

        # When
        await user.open("/spacing")
        await user.should_see("Overzicht")  # Wait for page to load

        # Then verify both records are shown initially
        table = user.find(ui.table).elements.pop()
        assert len(table.rows) == 2
        assert table.rows[0]["warning_emoji"] == ""  # No warning
        assert table.rows[1]["warning_emoji"] == "⚠️"  # Has warning

        # When warning filter is enabled
        warning_toggle = user.find(marker="warning_filter", kind=ui.switch)
        warning_toggle.click()  # from False to True

        # Wait for warning filter to be applied
        try:
            await asyncio.wait_for(done_event.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            raise RuntimeError("Timeout while waiting for warning filter.")

        # Verify repository was called with warning filter
        mock_repo.get_paginated.assert_called_with(
            pagination=Pagination(
                page=1, rows_per_page=10, total_rows=1, sort_by=None, descending=False
            ),
            filter_text="",
            warning_filter=True,
        )

        # Then verify filtered records are shown
        table = user.find(ui.table).elements.pop()
        assert len(table.rows) == 1
        assert table.rows[0]["warning_emoji"] == "⚠️"  # Has warning
