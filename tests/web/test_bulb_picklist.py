"""Tests for bulb picklist web interface."""

from datetime import date
from unittest.mock import patch, MagicMock

from nicegui import ui
from nicegui.testing import User

from production_control.bulb_picklist.models import BulbPickList


async def test_bulb_picklist_page_shows_table(user: User) -> None:
    """Test that bulb picklist page shows a table with bulb picklist data."""
    with patch(
        "production_control.web.pages.bulb_picklist.BulbPickListRepository"
    ) as mock_repo_class:
        # Given
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        test_date = date(2023, 1, 2)  # Monday of week 1, 2023
        mock_repo.get_paginated.return_value = (
            [
                BulbPickList(
                    id=1001,
                    bollen_code=12345,
                    ras="Tulipa Test",
                    locatie="A01-01",
                    aantal_bakken=10.0,
                    aantal_bollen=100.0,
                    oppot_datum=test_date,
                ),
                BulbPickList(
                    id=1002,
                    bollen_code=67890,
                    ras="Narcissus Demo",
                    locatie="B02-03",
                    aantal_bakken=15.0,
                    aantal_bollen=150.0,
                    oppot_datum=test_date,
                ),
            ],
            2,  # total count
        )

        # When
        await user.open("/bulb-picking")

        # Then
        table = user.find(ui.table).elements.pop()
        assert table.columns == [
            {
                "name": "id",
                "label": "ID",
                "field": "id",
                "sortable": True,
            },
            {
                "name": "bollen_code",
                "label": "Bollen Code",
                "field": "bollen_code",
                "sortable": True,
            },
            {
                "name": "ras",
                "label": "Ras",
                "field": "ras",
                "sortable": True,
            },
            {
                "name": "locatie",
                "label": "Locatie",
                "field": "locatie",
                "sortable": True,
            },
            {
                "name": "aantal_bakken",
                "label": "Aantal Bakken",
                "field": "aantal_bakken",
                "sortable": True,
            },
            {
                "name": "aantal_bollen",
                "label": "Aantal Bollen",
                "field": "aantal_bollen",
                "sortable": True,
            },
            {
                "name": "oppot_datum",
                "label": "Oppot Datum",
                "field": "oppot_datum",
                "sortable": True,
            },
            {"name": "actions", "label": "Acties", "field": "actions"},
        ]

        # Check essential visible fields in rows
        assert len(table.rows) == 2
        # Check row 0
        assert table.rows[0]["id"] == 1001
        assert table.rows[0]["bollen_code"] == 12345
        assert table.rows[0]["ras"] == "Tulipa Test"
        assert table.rows[0]["locatie"] == "A01-01"
        assert table.rows[0]["aantal_bakken"] == 10.0
        assert table.rows[0]["aantal_bollen"] == 100.0
        # Check row 1
        assert table.rows[1]["id"] == 1002
        assert table.rows[1]["bollen_code"] == 67890
        assert table.rows[1]["ras"] == "Narcissus Demo"
        assert table.rows[1]["locatie"] == "B02-03"
        assert table.rows[1]["aantal_bakken"] == 15.0
        assert table.rows[1]["aantal_bollen"] == 150.0
