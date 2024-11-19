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
from ..components.table_utils import format_row
from ..components.table_state import ClientStorageTableState


router = APIRouter(prefix="/spacing")


@router.page("/")
def spacing_page() -> None:
    """Render the spacing page with a table of all spacing records."""

    # Set up table data access
    repository = SpacingRepository()
    table_state = ClientStorageTableState.initialize("spacing_table")

    def load_data():
        pagination = table_state.pagination
        filter_text = table_state.filter
        items, total = repository.get_paginated(
            page=pagination.page,
            items_per_page=pagination.rows_per_page,
            sort_by=pagination.sort_by,
            descending=pagination.descending,
            filter_text=filter_text,
        )
        table_state.update_rows([format_row(item) for item in items], total)
        server_side_paginated_table.refresh()

    # event handlers
    async def handle_filter(e: Any) -> None:
        """Handle changes to the search filter."""
        table_state.update_filter(e.value if e.value else "")
        load_data()

    def handle_table_request(event: Dict[str, Any]) -> None:
        """Handle table request events."""
        table_state.update_from_request(event)
        load_data()

    # render page
    with frame("Wijderzetten"):
        with ui.card().classes(CARD_CLASSES.replace("max-w-3xl", "max-w-5xl")):
            with ui.row().classes("w-full justify-between items-center mb-4"):
                ui.label("Overzicht").classes(HEADER_CLASSES)
                ui.input(
                    placeholder="Zoek ...",
                    on_change=lambda e: handle_filter(e),
                ).classes("w-64").mark("search")

            server_side_paginated_table(
                WijderzetRegistratie,
                table_state,
                handle_table_request,
            )

    # load initial data
    load_data()
