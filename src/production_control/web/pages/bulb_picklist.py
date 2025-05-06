"""Bulb picklist page implementation."""

import os
from typing import Dict, Any

from nicegui import APIRouter, ui, app

from ...bulb_picklist.repositories import BulbPickListRepository
from ...bulb_picklist.models import BulbPickList
from ...bulb_picklist.label_generation import LabelGenerator
from ..components import frame
from ..components.styles import (
    CARD_CLASSES,
    HEADER_CLASSES,
    LINK_CLASSES,
)
from ..components.data_table import server_side_paginated_table
from ..components.table_utils import format_row
from ..components.table_state import ClientStorageTableState


router = APIRouter(prefix="/bulb-picking")


@router.page("/")
def bulb_picklist_page() -> None:
    """Render the bulb picklist page with a table of all bulb picklist records."""

    # Set up table data access
    repository = BulbPickListRepository()
    table_state = ClientStorageTableState.initialize("bulb_picklist_table")

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
    def handle_view(e: Dict[str, Any]) -> None:
        """Handle view button click."""
        id = e.args.get("key")
        record = repository.get_by_id(id)
        if record:
            with ui.dialog() as dialog, ui.card():
                ui.label(f"{record.ras} ({record.bollen_code})").classes(HEADER_CLASSES)
                ui.label(f"Locatie: {record.locatie}")
                ui.label(f"Aantal bakken: {record.aantal_bakken}")
                ui.label(f"Aantal bollen: {record.aantal_bollen}")
                ui.label(f"Oppot datum: {record.oppot_datum}")
                ui.button("Sluiten", on_click=dialog.close)
                dialog.open()

    # actions
    def handle_label(e: Dict[str, Any]) -> None:
        """Handle label button click."""
        id = e.args.get("key")
        record = repository.get_by_id(id)
        if record:
            # Generate PDF label directly without showing a dialog
            label_generator = LabelGenerator()

            # Get the base URL from environment variable, app.urls, or empty string
            base_url = os.environ.get("QR_CODE_BASE_URL", "")

            # If no env var, try to get from app.urls
            if not base_url:
                base_url = next(iter(app.urls), "")

            # Generate PDF in a temporary file
            pdf_path = label_generator.generate_pdf(record, base_url=base_url)

            # Create a download link for the PDF
            filename = f"label_{record.id}_{record.ras.replace(' ', '_')}.pdf"
            ui.download(pdf_path, filename=filename)

            # Clean up the temporary file after download
            # Note: This will run after the download is complete
            def cleanup():
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)

            ui.timer(5, cleanup, once=True)

    row_actions = {
        "view": {
            "icon": "visibility",
            "handler": handle_view,
        },
        "label": {
            "icon": "print",
            "handler": handle_label,
        },
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
    with frame("Bollen Picklist"):
        with ui.card().classes(CARD_CLASSES.replace("max-w-3xl", "max-w-7xl")):
            with ui.row().classes("w-full justify-between items-center mb-4"):
                ui.label("Overzicht").classes(HEADER_CLASSES)
                with ui.row().classes("gap-4"):
                    # Search input
                    with (
                        ui.input(
                            "Zoek ...",
                            on_change=lambda e: handle_filter(e),
                        )
                        .classes("w-64")
                        .mark("search") as search
                    ):
                        with search.add_slot("append"):
                            ui.icon("search")

            server_side_paginated_table(
                cls=BulbPickList,
                state=table_state,
                on_request=handle_table_request,
                row_actions=row_actions,
            )

    # load initial data
    load_data()


@router.page("/{id}")
def bulb_picklist_detail(id: int) -> None:
    """Render the bulb picklist record detail page."""
    repository = BulbPickListRepository()

    with frame("Bollen Picklist Details"):
        record = repository.get_by_id(id)

        if record:
            with ui.row().classes("w-full justify-between items-center mb-6"):
                ui.link("← Terug naar Bollen Picklist", "/bulb-picking").classes(LINK_CLASSES)

            with ui.card().classes(CARD_CLASSES):
                ui.label(f"{record.ras} ({record.bollen_code})").classes(HEADER_CLASSES)
                ui.label(f"Locatie: {record.locatie}")
                ui.label(f"Aantal bakken: {record.aantal_bakken}")
                ui.label(f"Aantal bollen: {record.aantal_bollen}")
                ui.label(f"Oppot datum: {record.oppot_datum}")
        else:
            ui.label("Record niet gevonden").classes("text-negative text-h6")
            ui.link("← Terug naar Bollen Picklist", "/bulb-picking").classes(LINK_CLASSES + " mt-4")


@router.page("/scan/{id}")
def bulb_picklist_scan(id: int) -> None:
    """Render the landing page for QR code scans."""
    repository = BulbPickListRepository()

    with frame("Bollen Picklist Scan"):
        record = repository.get_by_id(id)

        if record:
            with ui.row().classes("w-full justify-between items-center mb-6"):
                ui.link("← Terug naar Bollen Picklist", "/bulb-picking").classes(LINK_CLASSES)

            with ui.card().classes(CARD_CLASSES):
                ui.label(f"{record.ras} ({record.bollen_code})").classes(HEADER_CLASSES)
                ui.label(f"Locatie: {record.locatie}")
                ui.label(f"Aantal bakken: {record.aantal_bakken}")
                ui.label(f"Aantal bollen: {record.aantal_bollen}")
                ui.label(f"Oppot datum: {record.oppot_datum}")
        else:
            ui.label("Record niet gevonden").classes("text-negative text-h6")
            ui.link("← Terug naar Bollen Picklist", "/bulb-picking").classes(LINK_CLASSES + " mt-4")
