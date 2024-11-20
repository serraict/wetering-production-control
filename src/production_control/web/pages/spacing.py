"""Spacing page implementation."""

from typing import Dict, Any

from nicegui import APIRouter, ui

from ...spacing.models import SpacingRepository, WijderzetRegistratie
from ..components import frame
from ..components.model_card import display_model_card
from ..components.message import show_error
from ..components.styles import (
    CARD_CLASSES,
    HEADER_CLASSES,
    LINK_CLASSES,
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
            pagination=pagination,
            filter_text=filter_text,
        )
        table_state.update_rows([format_row(item) for item in items], total)
        server_side_paginated_table.refresh()

    # actions
    row_actions = {
        "view": {
            "icon": "visibility",
            "handler": lambda e: ui.navigate.to(f"/spacing/{e.args.get('key')}"),
        }
    }

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
        with ui.card().classes(CARD_CLASSES.replace("max-w-3xl", "max-w-7xl")):
            with ui.row().classes("w-full justify-between items-center mb-4"):
                ui.label("Overzicht").classes(HEADER_CLASSES)
                ui.input(
                    placeholder="Zoek ...",
                    on_change=lambda e: handle_filter(e),
                ).classes(
                    "w-64"
                ).mark("search")

            table = server_side_paginated_table(
                cls=WijderzetRegistratie,
                state=table_state,
                on_request=handle_table_request,
                row_actions=row_actions,
            )
            # Add styling for error rows
            table.add_slot(
                "body",
                """
                <tr :props="props" :class="{'bg-warning bg-opacity-10': props.row.wijderzet_registratie_fout}">
                    <q-td v-for="col in props.cols" :key="col.name" :props="props">
                        {{ col.value }}
                    </q-td>
                </tr>
            """,
            )

    # load initial data
    load_data()


@router.page("/{partij_code}")
def spacing_detail(partij_code: str) -> None:
    """Render the spacing record detail page."""
    repository = SpacingRepository()

    with frame("Wijderzet Details"):
        record = repository.get_by_id(partij_code)

        if record:
            with ui.row().classes("w-full justify-between items-center mb-6"):
                ui.link("← Terug naar Wijderzetten", "/spacing").classes(LINK_CLASSES)

            display_model_card(record, title=str(record))

            # Show error message if present
            if record.wijderzet_registratie_fout:
                with ui.card().classes("mt-4 bg-warning bg-opacity-10"):
                    ui.label("Fout").classes("text-lg font-bold")
                    ui.label(record.wijderzet_registratie_fout)
        else:
            show_error("Record niet gevonden")
            ui.link("← Terug naar Wijderzetten", "/spacing").classes(LINK_CLASSES + " mt-4")
