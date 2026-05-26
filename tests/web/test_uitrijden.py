"""Tests for the uitrijden web page."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

from nicegui import ui
from nicegui.testing import User

from production_control.vloerplan.models import Vloerplan19cm
from production_control.web.pages.uitrijden import (
    SYNC_RECENT_DAYS,
    default_sync_selection,
)


def _row(id: int, datum_oppot_plan):
    return Vloerplan19cm(
        id=id,
        tuin_nr_plan=1,
        tuin_nr_olsthoorn=2,
        datum_oppot_plan=datum_oppot_plan,
    )


def test_default_sync_selection_deselects_recent_pottings():
    """Rows potted in the last SYNC_RECENT_DAYS days are off by default."""
    today = date(2026, 5, 26)
    cutoff = today - timedelta(days=SYNC_RECENT_DAYS)

    rows = [
        _row(1, today),
        _row(2, today - timedelta(days=1)),
        _row(3, cutoff),
        _row(4, cutoff - timedelta(days=1)),
        _row(5, None),
    ]

    selected = default_sync_selection(rows, today)
    assert selected == {3, 4}


async def test_uitrijden_page_shows_table(user: User) -> None:
    """List page renders the table with rows from the repository."""
    with patch("production_control.web.pages.uitrijden.Vloerplan19cmRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.count_pending_olsthoorn_sync.return_value = 0
        mock_repo.get_paginated.return_value = (
            [
                Vloerplan19cm(
                    id=27515,
                    product_naam="S. Camino 19",
                    productgroep_naam="19 oriëntal",
                    klant_code=None,
                    tuin_nr_plan=3,
                    tuin_nr_olsthoorn=1,
                    datum_oppot_plan=date(2026, 2, 2),
                    datum_uit_cel_plan_opm=None,
                    opmerking=None,
                ),
            ],
            1,
        )

        await user.open("/uitrijden")
        await user.should_see("Uitrijden")

        table = user.find(ui.table).elements.pop()
        assert len(table.rows) == 1
        assert table.rows[0]["id"] == 27515
        assert table.rows[0]["product_naam"] == "S. Camino 19"
        assert table.rows[0]["productgroep_naam"] == "19 oriëntal"


async def test_uitrijden_detail_page_shows_record(user: User) -> None:
    """Detail page renders fields of the fetched record."""
    with patch("production_control.web.pages.uitrijden.Vloerplan19cmRepository") as mock_repo_class:
        mock_repo = MagicMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = Vloerplan19cm(
            id=27515,
            product_naam="S. Camino 19",
            productgroep_naam="19 oriëntal",
            klant_code=None,
            tuin_nr_plan=3,
            tuin_nr_olsthoorn=1,
            datum_oppot_plan=date(2026, 2, 2),
            datum_uit_cel_plan_opm=None,
            opmerking=None,
        )

        await user.open("/uitrijden/27515")

        await user.should_see("S. Camino 19")
        await user.should_see("← Terug naar Uitrijden")
