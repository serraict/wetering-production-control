"""Spacing page implementation."""

from typing import Dict, Any

from nicegui import APIRouter, ui

from ...spacing.models import SpacingRepository, WijderzetRegistratie
from ..components import frame
from ..components.styles import (
    CARD_CLASSES,
    HEADER_CLASSES,
)
from ..components.data_table import server_side_paginated_table
from ..components.table_state import ClientStorageTableState


router = APIRouter(prefix="/spacing")


def format_row(registratie: WijderzetRegistratie) -> Dict[str, Any]:
    """Format spacing record for table display."""
    return {
        "id": registratie.id,
        "partij_code": registratie.partij_code,
        "product_naam": registratie.product_naam,
        "productgroep_naam": registratie.productgroep_naam,
        "datum_oppotten_real": registratie.datum_oppotten_real,
        "datum_uit_cel_real": registratie.datum_uit_cel_real,
        "datum_wdz1_real": registratie.datum_wdz1_real,
        "datum_wdz2_real": registratie.datum_wdz2_real,
        "aantal_planten_gerealiseerd": registratie.aantal_planten_gerealiseerd,
        "aantal_tafels_totaal": registratie.aantal_tafels_totaal,
        "aantal_tafels_na_wdz1": registratie.aantal_tafels_na_wdz1,
        "aantal_tafels_na_wdz2": registratie.aantal_tafels_na_wdz2,
        "aantal_tafels_oppotten_plan": registratie.aantal_tafels_oppotten_plan,
        "dichtheid_oppotten_plan": registratie.dichtheid_oppotten_plan,
        "dichtheid_wz1_plan": registratie.dichtheid_wz1_plan,
        "dichtheid_wz2_plan": registratie.dichtheid_wz2_plan,
        "wijderzet_registratie_fout": registratie.wijderzet_registratie_fout,
    }


@router.page("/")
def spacing_page() -> None:
    """Render the spacing page with a table of all spacing records."""
    repository = SpacingRepository()
    table_state = ClientStorageTableState.initialize("spacing_table")

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

            async def handle_filter(e: Any) -> None:
                """Handle changes to the search filter with debounce."""
                table_state.update_filter(e.value if e.value else "")
                table_state.pagination.page = 1  # Reset to first page
                load_filtered_data()

            def handle_table_request(event: Dict[str, Any]) -> None:
                """Handle table request events (pagination and sorting)."""
                # Update pagination state from request
                table_state.update_from_request(event)

                # Get new page of data with sorting
                registraties, total = repository.get_paginated(
                    page=table_state.pagination.page,
                    items_per_page=table_state.pagination.rows_per_page,
                    sort_by=table_state.pagination.sort_by,
                    descending=table_state.pagination.descending,
                    filter_text=table_state.filter,
                )

                # Update table data
                table_state.update_rows([format_row(r) for r in registraties], total)

                # Refresh the table UI
                server_side_paginated_table.refresh()

            def load_filtered_data() -> None:
                """Load data with current filter and refresh table."""
                handle_table_request({"pagination": table_state.pagination.to_dict()})

            # Initial data load
            def load_initial_data() -> None:
                """Load initial data and set total count."""
                registraties, total = repository.get_paginated(page=1, items_per_page=10)
                table_state.update_rows([format_row(r) for r in registraties], total)
                server_side_paginated_table.refresh()

            # Create table and load data
            server_side_paginated_table(
                WijderzetRegistratie,
                table_state,
                handle_table_request,
                title="Wijderzetten",
            )
            load_initial_data()
