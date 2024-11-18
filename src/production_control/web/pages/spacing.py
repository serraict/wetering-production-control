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
        "rowsNumber": 0,  # This will signal the Quasar component to use server side pagination
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
            with ui.row().classes("w-full justify-between items-center mb-4"):
                ui.label("Wijderzetten Overzicht").classes(HEADER_CLASSES)
                # Add search input with debounce
                ui.input(
                    placeholder="Zoek wijderzet registraties...",
                    on_change=lambda e: handle_filter(e),
                ).classes("w-64").mark("search")

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
                    "name": "datum_oppotten_real",
                    "label": "Datum Oppotten",
                    "field": "datum_oppotten_real",
                    "sortable": True,
                },
                {
                    "name": "datum_uit_cel_real",
                    "label": "Datum Uit Cel",
                    "field": "datum_uit_cel_real",
                    "sortable": True,
                },
                {
                    "name": "datum_wdz1_real",
                    "label": "Datum WDZ1",
                    "field": "datum_wdz1_real",
                    "sortable": True,
                },
                {
                    "name": "datum_wdz2_real",
                    "label": "Datum WDZ2",
                    "field": "datum_wdz2_real",
                    "sortable": True,
                },
                {
                    "name": "aantal_planten_gerealiseerd",
                    "label": "Aantal Planten",
                    "field": "aantal_planten_gerealiseerd",
                    "sortable": True,
                },
                {
                    "name": "aantal_tafels_totaal",
                    "label": "Totaal Tafels",
                    "field": "aantal_tafels_totaal",
                    "sortable": True,
                },
                {
                    "name": "aantal_tafels_na_wdz1",
                    "label": "Tafels Na WDZ1",
                    "field": "aantal_tafels_na_wdz1",
                    "sortable": True,
                },
                {
                    "name": "aantal_tafels_na_wdz2",
                    "label": "Tafels Na WDZ2",
                    "field": "aantal_tafels_na_wdz2",
                    "sortable": True,
                },
                {
                    "name": "aantal_tafels_oppotten_plan",
                    "label": "Tafels Oppotten Plan",
                    "field": "aantal_tafels_oppotten_plan",
                    "sortable": True,
                },
                {
                    "name": "dichtheid_oppotten_plan",
                    "label": "Dichtheid Oppotten",
                    "field": "dichtheid_oppotten_plan",
                    "sortable": True,
                },
                {
                    "name": "dichtheid_wz1_plan",
                    "label": "Dichtheid WDZ1",
                    "field": "dichtheid_wz1_plan",
                    "sortable": True,
                },
                {
                    "name": "dichtheid_wz2_plan",
                    "label": "Dichtheid WDZ2",
                    "field": "dichtheid_wz2_plan",
                    "sortable": True,
                },
                {
                    "name": "wijderzet_registratie_fout",
                    "label": "Heeft Fout",
                    "field": "wijderzet_registratie_fout",
                },
                {"name": "actions", "label": "Acties", "field": "actions"},
            ]

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
                        "id": str(r.id),  # Convert UUID to string for JSON
                        "partij_code": r.partij_code,
                        "product_naam": r.product_naam,
                        "productgroep_naam": r.productgroep_naam,
                        "datum_oppotten_real": r.datum_oppotten_real.isoformat(),
                        "datum_uit_cel_real": r.datum_uit_cel_real.isoformat(),
                        "datum_wdz1_real": r.datum_wdz1_real.isoformat(),
                        "datum_wdz2_real": r.datum_wdz2_real.isoformat(),
                        "aantal_planten_gerealiseerd": r.aantal_planten_gerealiseerd,
                        "aantal_tafels_totaal": r.aantal_tafels_totaal,
                        "aantal_tafels_na_wdz1": r.aantal_tafels_na_wdz1,
                        "aantal_tafels_na_wdz2": r.aantal_tafels_na_wdz2,
                        "aantal_tafels_oppotten_plan": str(r.aantal_tafels_oppotten_plan),
                        "dichtheid_oppotten_plan": r.dichtheid_oppotten_plan,
                        "dichtheid_wz1_plan": r.dichtheid_wz1_plan,
                        "dichtheid_wz2_plan": r.dichtheid_wz2_plan,
                        "wijderzet_registratie_fout": r.wijderzet_registratie_fout,
                    }
                    for r in registraties
                ]
                table_data["pagination"]["rowsNumber"] = total
                spacing_table.refresh()

            async def handle_filter(e: Any) -> None:
                """Handle changes to the search filter with debounce."""
                table_data["filter"] = e.value if e.value else ""
                table_data["pagination"]["page"] = 1  # Reset to first page
                load_filtered_data()

            def load_filtered_data() -> None:
                """Load data with current filter and refresh table."""
                handle_table_request({"pagination": table_data["pagination"]})

            def load_initial_data() -> None:
                """Load initial data and set total count."""
                registraties, total = repository.get_paginated(page=1, items_per_page=10)
                table_data["rows"] = [
                    {
                        "id": str(r.id),  # Convert UUID to string for JSON
                        "partij_code": r.partij_code,
                        "product_naam": r.product_naam,
                        "productgroep_naam": r.productgroep_naam,
                        "datum_oppotten_real": r.datum_oppotten_real.isoformat(),
                        "datum_uit_cel_real": r.datum_uit_cel_real.isoformat(),
                        "datum_wdz1_real": r.datum_wdz1_real.isoformat(),
                        "datum_wdz2_real": r.datum_wdz2_real.isoformat(),
                        "aantal_planten_gerealiseerd": r.aantal_planten_gerealiseerd,
                        "aantal_tafels_totaal": r.aantal_tafels_totaal,
                        "aantal_tafels_na_wdz1": r.aantal_tafels_na_wdz1,
                        "aantal_tafels_na_wdz2": r.aantal_tafels_na_wdz2,
                        "aantal_tafels_oppotten_plan": str(r.aantal_tafels_oppotten_plan),
                        "dichtheid_oppotten_plan": r.dichtheid_oppotten_plan,
                        "dichtheid_wz1_plan": r.dichtheid_wz1_plan,
                        "dichtheid_wz2_plan": r.dichtheid_wz2_plan,
                        "wijderzet_registratie_fout": r.wijderzet_registratie_fout,
                    }
                    for r in registraties
                ]
                table_data["pagination"]["rowsNumber"] = total
                spacing_table.refresh()

            @ui.refreshable
            def spacing_table() -> ui.table:
                """Create a refreshable table component."""
                table = ui.table(
                    columns=columns,
                    rows=table_data["rows"] if "rows" in table_data else [],
                    row_key="id",
                    pagination=table_data["pagination"],
                ).classes("w-full")
                table.on("request", handle_table_request)
                return table

            # Create table and load data
            table = spacing_table()
            load_initial_data()

            return table
