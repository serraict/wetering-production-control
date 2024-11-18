"""Spacing page implementation."""

from typing import Dict, Any

from nicegui import APIRouter, ui

from ...spacing.models import SpacingRepository, WijderzetRegistratie
from ..components import frame
from ..components.styles import (
    CARD_CLASSES,
    HEADER_CLASSES,
)
from ..components.table_utils import get_table_columns


router = APIRouter(prefix="/spacing")

# Shared table state
table_data = {
    "pagination": {
        "rowsPerPage": 10,
        "page": 1,
        "rowsNumber": 0,  # This will signal the Quasar component to use server side pagination
        "sortBy": None,
        "descending": False,
    },
    "filter": "",  # Single filter for searching all fields
}


@router.page("/")
def spacing_page() -> None:
    """Render the spacing page with a table of all spacing records."""
    repository = SpacingRepository()

    with frame("Spacing"):
        with ui.card().classes(CARD_CLASSES.replace("max-w-3xl", "max-w-5xl")):
            # Header section
            with ui.row().classes("w-full justify-between items-center mb-4"):
                ui.label("Wijderzetten Overzicht").classes(HEADER_CLASSES)
                # Add search input with debounce
                ui.input(
                    placeholder="Search spacing records...",
                    on_change=lambda e: handle_filter(e),
                ).classes("w-64").mark("search")

            @ui.refreshable
            def spacing_table() -> ui.table:
                """Create a refreshable table component."""
                columns = get_table_columns(WijderzetRegistratie)
                table = ui.table(
                    columns=columns,
                    rows=table_data["rows"] if "rows" in table_data else [],
                    row_key="id",
                    pagination=table_data["pagination"],
                ).classes("w-full")
                table.on("request", handle_table_request)
                return table

            async def handle_filter(e: Any) -> None:
                """Handle changes to the search filter with debounce."""
                table_data["filter"] = e.value if e.value else ""
                table_data["pagination"]["page"] = 1  # Reset to first page
                load_filtered_data()

            def handle_table_request(event: Dict[str, Any]) -> None:
                """Handle table request events (pagination and sorting)."""
                # Update pagination state from request
                new_pagination = (
                    event["pagination"] if isinstance(event, dict) else event.args["pagination"]
                )
                table_data["pagination"].update(new_pagination)

                # Get new page of data with sorting
                page = new_pagination.get("page", 1)
                rows_per_page = new_pagination.get("rowsPerPage", 10)
                sort_by = new_pagination.get("sortBy")
                descending = new_pagination.get("descending", False)

                registraties, total = repository.get_paginated(
                    page=page,
                    items_per_page=rows_per_page,
                    sort_by=sort_by,
                    descending=descending,
                    filter_text=table_data["filter"],
                )

                # Update table data
                table_data["rows"] = [
                    {
                        "id": r.id,
                        "partij_code": r.partij_code,
                        "product_naam": r.product_naam,
                        "productgroep_naam": r.productgroep_naam,
                        "datum_oppotten_real": r.datum_oppotten_real,
                        "datum_uit_cel_real": r.datum_uit_cel_real,
                        "datum_wdz1_real": r.datum_wdz1_real,
                        "datum_wdz2_real": r.datum_wdz2_real,
                        "aantal_planten_gerealiseerd": r.aantal_planten_gerealiseerd,
                        "aantal_tafels_totaal": r.aantal_tafels_totaal,
                        "aantal_tafels_na_wdz1": r.aantal_tafels_na_wdz1,
                        "aantal_tafels_na_wdz2": r.aantal_tafels_na_wdz2,
                        "aantal_tafels_oppotten_plan": r.aantal_tafels_oppotten_plan,
                        "dichtheid_oppotten_plan": r.dichtheid_oppotten_plan,
                        "dichtheid_wz1_plan": r.dichtheid_wz1_plan,
                        "dichtheid_wz2_plan": r.dichtheid_wz2_plan,
                        "wijderzet_registratie_fout": r.wijderzet_registratie_fout,
                    }
                    for r in registraties
                ]
                table_data["pagination"]["rowsNumber"] = total

                # Refresh the table UI
                spacing_table.refresh()

            def load_filtered_data() -> None:
                """Load data with current filter and refresh table."""
                handle_table_request({"pagination": table_data["pagination"]})

            # Initial data load
            def load_initial_data() -> None:
                """Load initial data and set total count."""
                registraties, total = repository.get_paginated(page=1, items_per_page=10)
                table_data["rows"] = [
                    {
                        "id": r.id,
                        "partij_code": r.partij_code,
                        "product_naam": r.product_naam,
                        "productgroep_naam": r.productgroep_naam,
                        "datum_oppotten_real": r.datum_oppotten_real,
                        "datum_uit_cel_real": r.datum_uit_cel_real,
                        "datum_wdz1_real": r.datum_wdz1_real,
                        "datum_wdz2_real": r.datum_wdz2_real,
                        "aantal_planten_gerealiseerd": r.aantal_planten_gerealiseerd,
                        "aantal_tafels_totaal": r.aantal_tafels_totaal,
                        "aantal_tafels_na_wdz1": r.aantal_tafels_na_wdz1,
                        "aantal_tafels_na_wdz2": r.aantal_tafels_na_wdz2,
                        "aantal_tafels_oppotten_plan": r.aantal_tafels_oppotten_plan,
                        "dichtheid_oppotten_plan": r.dichtheid_oppotten_plan,
                        "dichtheid_wz1_plan": r.dichtheid_wz1_plan,
                        "dichtheid_wz2_plan": r.dichtheid_wz2_plan,
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
