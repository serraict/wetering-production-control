"""Tests for spacing page."""

import asyncio
from datetime import date
from decimal import Decimal
from typing import Optional
from unittest.mock import patch, Mock

from nicegui import ui
from nicegui.testing import User

from production_control.data import Pagination
from production_control.spacing.models import WijderzetRegistratie


async def test_spacing_page_shows_table(user: User) -> None:
    """Test that spacing page shows a table with spacing data."""
    with patch("production_control.web.pages.spacing.SpacingRepository") as mock_repo_class:
        # Given
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        test_date = date(2023, 1, 1)
        mock_repo.get_paginated.return_value = (
            [
                WijderzetRegistratie(
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
                ),
                WijderzetRegistratie(
                    partij_code="TEST456",
                    product_naam="Other Plant",
                    productgroep_naam="Other Group",
                    aantal_tafels_totaal=20,
                    aantal_tafels_na_wdz1=25,
                    aantal_tafels_na_wdz2=30,
                    aantal_tafels_oppotten_plan=Decimal("20.0"),
                    aantal_planten_gerealiseerd=200,
                    datum_wdz1_real=test_date,
                    datum_wdz2_real=test_date,
                    datum_oppotten_real=test_date,
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
                "name": "productgroep_naam",
                "label": "Productgroep",
                "field": "productgroep_naam",
                "sortable": True,
            },
            {
                "name": "aantal_tafels_totaal",
                "label": "Tafels totaal",
                "field": "aantal_tafels_totaal",
                "sortable": True,
            },
            {
                "name": "aantal_tafels_na_wdz1",
                "label": "Tafels na WZ1",
                "field": "aantal_tafels_na_wdz1",
                "sortable": True,
            },
            {
                "name": "aantal_tafels_na_wdz2",
                "label": "Tafels na WZ2",
                "field": "aantal_tafels_na_wdz2",
                "sortable": True,
            },
            {
                "name": "aantal_tafels_oppotten_plan",
                "label": "Tafels plan",
                "field": "aantal_tafels_oppotten_plan",
                "sortable": True,
            },
            {
                "name": "aantal_planten_gerealiseerd",
                "label": "Planten",
                "field": "aantal_planten_gerealiseerd",
                "sortable": True,
            },
            {
                "name": "datum_wdz1_real",
                "label": "Wijderzet 1",
                "field": "datum_wdz1_real",
                "sortable": True,
                ":format": "value => value ? Quasar.date.formatDate(value, 'YY[w]ww-E') : ''",
            },
            {
                "name": "datum_wdz2_real",
                "label": "Wijderzet 2",
                "field": "datum_wdz2_real",
                "sortable": True,
                ":format": "value => value ? Quasar.date.formatDate(value, 'YY[w]ww-E') : ''",
            },
            {"name": "actions", "label": "Acties", "field": "actions"},
        ]

        # Check essential visible fields in rows
        assert len(table.rows) == 2
        assert table.rows[0]["partij_code"] == "TEST123"
        assert table.rows[0]["product_naam"] == "Test Plant"
        assert table.rows[0]["aantal_tafels_totaal"] == 10

        assert table.rows[1]["partij_code"] == "TEST456"
        assert table.rows[1]["product_naam"] == "Other Plant"
        assert table.rows[1]["aantal_tafels_totaal"] == 20


async def test_spacing_page_filtering_calls_repository(user: User) -> None:
    """Test that entering a filter value calls the repository with the filter text."""
    with patch("production_control.web.pages.spacing.SpacingRepository") as mock_repo_class:
        # Given
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_paginated.return_value = ([], 0)  # Empty initial result

        # An asyncio.Event to signal when the repository is called with filter
        done_event = asyncio.Event()

        def on_get_paginated(
            pagination: Optional[Pagination] = None,
            page: int = 1,
            items_per_page: int = 10,
            sort_by: Optional[str] = None,
            descending: bool = False,
            filter_text: str = "",
        ):
            if filter_text == "TEST123":
                done_event.set()  # Set the event when desired call is made
            return [], 0

        mock_repo.get_paginated.side_effect = on_get_paginated

        # When
        await user.open("/spacing")
        search_box = user.find(marker="search", kind=ui.input)
        search_box.type("TEST123")
        search_box.trigger("change")

        # Await until the event is set, or timeout if necessary
        try:
            await asyncio.wait_for(done_event.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            raise RuntimeError("Timeout while waiting for repository call.")

        # Then verify repository was called with filter
        mock_repo.get_paginated.assert_called_with(
            pagination=Pagination(
                page=1, rows_per_page=10, total_rows=0, sort_by=None, descending=False
            ),
            filter_text="TEST123",
        )
