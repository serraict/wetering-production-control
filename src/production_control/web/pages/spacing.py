"""Spacing page implementation."""

from datetime import date, timedelta
from typing import Dict, Any, Callable

from nicegui import APIRouter, ui
from pydantic import ValidationError

from ...spacing.repositories import SpacingRepository
from ...spacing.models import WijderzetRegistratie
from ...spacing.commands import CorrectSpacingRecord
from ...spacing.optech import OpTechClient, OpTechError
from ..components import frame
from ..components.model_card import display_model_card
from ..components.message import show_error
from ..components.command_form import create_command_form
from ..components.model_detail_page import display_model_detail_page, create_model_view_action
from ..components.model_list_page import display_model_list_page
from ..components.table_utils import format_row


router = APIRouter(prefix="/spacing")


def create_correction_form(record: WijderzetRegistratie, on_close: Callable[[], None]) -> None:
    """Create the correction form for a spacing record.

    Args:
        record: The record to correct
        on_close: Callback to handle closing the form (e.g. close dialog or navigate back)
    """
    # Title
    ui.label(f"{record.partij_code} - {record.product_naam}").classes("text-h6 font-bold mb-4")

    # Show error message if present
    if record.wijderzet_registratie_fout:
        with ui.card().classes("mb-4 bg-warning bg-opacity-10"):
            ui.label("Fout").classes("text-lg font-bold")
            ui.label(record.wijderzet_registratie_fout)

    # Create command and form
    client = OpTechClient()
    command = CorrectSpacingRecord.from_record(record)

    def handle_save(updated: CorrectSpacingRecord) -> None:
        """Handle save button click."""
        try:
            client.send_correction(updated)
            ui.notify(f"Wijzigingen opgeslagen voor {record.partij_code}")
            on_close()
        except ValidationError as e:
            # Show first error message
            error = e.errors()[0]
            ui.notify(error["msg"], type="negative", timeout=5000)
        except OpTechError as e:
            ui.notify(str(e), type="negative", timeout=5000)

    create_command_form(command, handle_save, on_close)


def display_spacing_record(record: WijderzetRegistratie) -> None:
    """Display a spacing record in a card.

    Args:
        record: The record to display
    """
    if record.wijderzet_registratie_fout:
        with ui.card().classes("mt-4 bg-warning bg-opacity-10"):
            ui.label("Fout").classes("text-lg font-bold")
            ui.label(record.wijderzet_registratie_fout)

    display_model_card(record, title=str(record))


def create_edit_action(repository: SpacingRepository) -> Dict[str, Any]:
    """Create an edit action for spacing records.

    Args:
        repository: The repository to use for fetching records

    Returns:
        A dictionary with the edit action configuration
    """

    def handle_edit(e: Dict[str, Any]) -> None:
        """Handle edit button click."""
        partij_code = e.args.get("key")
        record = repository.get_by_id(partij_code)
        if record:
            with ui.dialog() as dialog, ui.card():
                create_correction_form(record, dialog.close)
                dialog.open()
        else:
            show_error("Record niet gevonden")

    return {
        "icon": "edit",
        "handler": handle_edit,
    }


def create_spacing_filters(row: ui.row, handle_warning_filter: Callable) -> None:
    """Create custom filters for the spacing page.

    Args:
        row: The row to add the filters to
        handle_warning_filter: Function to handle warning filter changes
    """
    # Date range inputs
    with ui.row().classes("items-center gap-2"):
        with ui.input("Van ...").classes("w-32").mark("date_from") as date_from:
            with ui.menu().props("no-parent-event") as menu_from:
                with ui.date(value=date.today() - timedelta(days=14)).bind_value(date_from):
                    with ui.row().classes("justify-end"):
                        ui.button("Sluiten", on_click=menu_from.close).props("flat")
            with date_from.add_slot("append"):
                ui.icon("edit_calendar").on("click", menu_from.open).classes("cursor-pointer")

    with ui.row().classes("items-center gap-2"):
        with ui.input("Tot ...").classes("w-32").mark("date_to") as date_to:
            with ui.menu().props("no-parent-event") as menu_to:
                with ui.date(value=date.today()).bind_value(date_to):
                    with ui.row().classes("justify-end"):
                        ui.button("Sluiten", on_click=menu_to.close).props("flat")
            with date_to.add_slot("append"):
                ui.icon("edit_calendar").on("click", menu_to.open).classes("cursor-pointer")

    # Warning filter
    ui.switch("Toon alleen waarschuwingen", on_change=handle_warning_filter).classes("mr-4").mark(
        "warning_filter"
    )


@router.page("/")
def spacing_page() -> None:
    """Render the spacing page with a table of all spacing records."""
    repository = SpacingRepository()

    # Set up table state
    from ..components.table_state import ClientStorageTableState

    table_state = ClientStorageTableState.initialize("spacing_table")

    # Override the load_data function in display_model_list_page
    def custom_load_data(repository, table_state):
        def load_data():
            pagination = table_state.pagination
            filter_text = table_state.filter
            warning_filter = getattr(table_state, "warning_filter", False)
            items, total = repository.get_paginated(
                pagination=pagination,
                filter_text=filter_text,
                warning_filter=warning_filter,
            )
            table_state.update_rows([format_row(item) for item in items], total)
            from ..components.data_table import server_side_paginated_table

            server_side_paginated_table.refresh()

        return load_data

    # Store the load_data function so we can call it from handle_warning_filter
    load_data_func = None

    def store_load_data(func):
        nonlocal load_data_func
        load_data_func = func
        return func

    # Custom filter handler for warnings
    async def handle_warning_filter(e: Any) -> None:
        """Handle changes to the warning filter."""
        table_state.update_warning_filter(e.value if e.value else False)
        # Call the load_data function directly
        if load_data_func:
            load_data_func()

    # Create actions
    row_actions = {
        "view": create_model_view_action(
            repository=repository,
            dialog=True,
            custom_display_function=display_spacing_record,
        ),
        "edit": create_edit_action(repository),
    }

    # Render page
    with frame("Wijderzetten"):
        display_model_list_page(
            repository=repository,
            model_cls=WijderzetRegistratie,
            table_state_key="spacing_table",
            title="Wijderzetten",
            row_actions=row_actions,
            card_width="max-w-7xl",
            filter_placeholder="Zoek ...",
            custom_filters=lambda row: create_spacing_filters(row, handle_warning_filter),
            custom_load_data=custom_load_data,
        )


@router.page("/{partij_code}")
def spacing_detail(partij_code: str) -> None:
    """Render the spacing record detail page."""
    repository = SpacingRepository()
    record = repository.get_by_id(partij_code)

    with frame("Wijderzet Details"):
        display_model_detail_page(
            model=record,
            title="Wijderzet Details",
            back_link_text="← Terug naar Wijderzetten",
            back_link_url="/spacing",
            custom_display_function=display_spacing_record,
        )


@router.page("/correct/{partij_code}")
def spacing_correct(partij_code: str) -> None:
    """Render the spacing record correction page."""
    repository = SpacingRepository()
    record = repository.get_by_id(partij_code)

    with frame("Wijderzet Correctie"):
        if record:
            with ui.row().classes("w-full justify-between items-center mb-6"):
                ui.link("← Terug naar Wijderzetten", "/spacing").classes(
                    "text-blue-500 hover:underline"
                )

            with ui.card().classes("p-4 max-w-3xl mx-auto"):
                create_correction_form(record, lambda: ui.navigate.to("/spacing"))
        else:
            ui.label("Record niet gevonden").classes("text-negative text-h6")
            ui.link("← Terug naar Wijderzetten", "/spacing").classes(
                "text-blue-500 hover:underline mt-4"
            )
