"""Spacing page implementation."""

from typing import List, Dict, Any

from nicegui import APIRouter, ui

from ...spacing.models import SpacingRepository
from ..components import frame
from ..components.styles import CARD_CLASSES, HEADER_CLASSES


router = APIRouter(prefix="/spacing")

# Shared table state
table_data = {
    "pagination": {
        "rowsPerPage": 10,
        "page": 1,
        "rowsNumber": 0,
        "sortBy": None,
        "descending": False,
    },
    "filter": "",
}


@router.page("/")
def spacing_page() -> None:
    """Render the spacing page."""
    repository = SpacingRepository()

    with frame("Spacing"):
        with ui.card().classes(CARD_CLASSES.replace("max-w-3xl", "max-w-5xl")):
            # Header section
            ui.label("Wijderzetten Overzicht").classes(HEADER_CLASSES)

            columns: List[Dict[str, Any]] = [
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

            @ui.refreshable
            def spacing_table() -> ui.table:
                """Create a refreshable table component."""
                table = ui.table(
                    columns=columns,
                    rows=table_data["rows"] if "rows" in table_data else [],
                    row_key="id",
                    pagination=table_data["pagination"],
                ).classes("w-full")
                return table

            def load_initial_data() -> None:
                """Load initial data and set total count."""
                registraties, total = repository.get_paginated(page=1, items_per_page=10)
                table_data["rows"] = [
                    {
                        "id": str(r.id),  # Convert UUID to string for JSON
                        "partij_code": r.partij_code,
                        "product_naam": r.product_naam,
                        "productgroep_naam": r.productgroep_naam,
                        "aantal_tafels_totaal": r.aantal_tafels_totaal,
                        "wijderzet_registratie_fout": r.wijderzet_registratie_fout,
                    }
                    for r in registraties
                ]
                table_data["pagination"]["rowsNumber"] = total
                spacing_table.refresh()

            # Create table and load data
            table = spacing_table()
            load_initial_data()

            return table
