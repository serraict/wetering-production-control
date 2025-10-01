"""Inspectie page implementation."""

from typing import Dict, Any, List

from nicegui import APIRouter, ui, app

from ...inspectie.repositories import InspectieRepository
from ...inspectie.models import InspectieRonde
from ...inspectie.commands import UpdateAfwijkingCommand
from ..components import frame
from ..components.model_list_page import display_model_list_page
from ..components.styles import add_print_styles


router = APIRouter(prefix="/inspectie")

# Fallback storage when app.storage.user is not available
_fallback_storage: Dict[str, Any] = {}


def get_storage() -> Dict[str, Any]:
    """Get storage safely, falling back to in-memory storage if needed."""
    try:
        return app.storage.user
    except RuntimeError:
        # Fallback to in-memory storage when storage_secret is not configured
        return _fallback_storage


def get_pending_commands() -> List[UpdateAfwijkingCommand]:
    """Get all pending afwijking commands from browser storage."""
    storage = get_storage()
    if "inspectie_changes" not in storage:
        return []

    commands = []
    for code, new_afwijking in storage["inspectie_changes"].items():
        commands.append(UpdateAfwijkingCommand(code=code, new_afwijking=new_afwijking))

    return commands


def clear_pending_commands() -> None:
    """Clear all pending commands from browser storage."""
    storage = get_storage()
    if "inspectie_changes" in storage:
        del storage["inspectie_changes"]


def get_filter_state() -> str:
    """Get current filter state from browser storage."""
    storage = get_storage()
    return storage.get("inspectie_filter", "next_two_weeks")


def set_filter_state(filter_state: str) -> None:
    """Set filter state in browser storage."""
    storage = get_storage()
    storage["inspectie_filter"] = filter_state


def toggle_filter() -> None:
    """Toggle between 'next_two_weeks' and 'show_all' filters."""
    current_state = get_filter_state()
    new_state = "show_all" if current_state == "next_two_weeks" else "next_two_weeks"
    set_filter_state(new_state)

    # Refresh the page to apply the new filter
    ui.run_javascript("location.reload()")


def create_enhanced_repository() -> InspectieRepository:
    """Create repository with current filter state applied."""
    repository = InspectieRepository()
    filter_state = get_filter_state()

    # Apply default filter if set to next_two_weeks
    if filter_state == "next_two_weeks":
        # Monkey patch the get_paginated method to apply default filter
        original_get_paginated = repository.get_paginated

        def get_paginated_with_filter(*args, **kwargs):
            if "default_filter" not in kwargs:
                kwargs["default_filter"] = "next_two_weeks"
            return original_get_paginated(*args, **kwargs)

        repository.get_paginated = get_paginated_with_filter

    return repository


def show_pending_changes_dialog(changes_state=None) -> None:
    """Show a dialog with all pending changes."""
    storage = get_storage()
    changes = storage.get("inspectie_changes", {})

    with ui.dialog() as dialog, ui.card().classes("w-96"):
        ui.label("Openstaande wijzigingen").classes("text-h6 mb-4")

        if not changes:
            ui.label("Geen openstaande wijzigingen").classes("text-center text-gray-500")
        else:
            # Create table with pending changes
            columns = [
                {
                    "name": "code",
                    "label": "Code",
                    "field": "code",
                    "required": True,
                    "align": "left",
                },
                {
                    "name": "change",
                    "label": "Wijziging",
                    "field": "change",
                    "required": True,
                    "align": "center",
                },
            ]

            rows = [{"code": code, "change": f"{change:+d}"} for code, change in changes.items()]

            ui.table(columns=columns, rows=rows, row_key="code").classes("w-full")

            ui.separator().classes("my-4")

            # Action buttons
            with ui.row().classes("w-full justify-between"):
                ui.button(
                    "Alles wissen",
                    icon="clear_all",
                    color="negative",
                    on_click=lambda: handle_clear_all_changes_and_close(dialog, changes_state),
                ).props("outline")

        # Close button
        with ui.row().classes("w-full justify-end mt-4"):
            ui.button("Sluiten", on_click=dialog.close).props("flat")

    dialog.open()


def handle_clear_all_changes(changes_state=None) -> None:
    """Handle clearing all pending changes."""
    clear_pending_commands()
    ui.notify("Alle wijzigingen gewist", type="info")
    # Update changes state if provided
    if changes_state:
        changes_state.update()


def handle_clear_all_changes_and_close(dialog, changes_state=None) -> None:
    """Handle clearing all changes and closing the dialog."""
    handle_clear_all_changes(changes_state)
    dialog.close()


def create_afwijking_actions(changes_state=None) -> Dict[str, Any]:
    """Create row actions for +1/-1 buttons."""

    def handle_plus_one(e: Dict[str, Any]) -> None:
        """Handle +1 button click."""
        code = e.args.get("key")
        if not code:
            ui.notify("Geen code gevonden", type="negative")
            return

        # Get storage safely
        storage = get_storage()

        # Initialize storage if needed
        if "inspectie_changes" not in storage:
            storage["inspectie_changes"] = {}

        # Update change tracking (+1)
        current_change = storage["inspectie_changes"].get(code, 0)
        storage["inspectie_changes"][code] = current_change + 1

        # Create and store command
        command = UpdateAfwijkingCommand(
            code=code, new_afwijking=storage["inspectie_changes"][code]
        )

        ui.notify(f"Afwijking +1 voor {code} (totaal: {command.new_afwijking})", type="positive")

        # Update changes state if provided
        if changes_state:
            changes_state.update()

    def handle_minus_one(e: Dict[str, Any]) -> None:
        """Handle -1 button click."""
        code = e.args.get("key")
        if not code:
            ui.notify("Geen code gevonden", type="negative")
            return

        # Get storage safely
        storage = get_storage()

        # Initialize storage if needed
        if "inspectie_changes" not in storage:
            storage["inspectie_changes"] = {}

        # Update change tracking (-1)
        current_change = storage["inspectie_changes"].get(code, 0)
        storage["inspectie_changes"][code] = current_change - 1

        # Create and store command
        command = UpdateAfwijkingCommand(
            code=code, new_afwijking=storage["inspectie_changes"][code]
        )

        ui.notify(f"Afwijking -1 voor {code} (totaal: {command.new_afwijking})", type="positive")

        # Update changes state if provided
        if changes_state:
            changes_state.update()

    return {
        "plus_one": {
            "icon": "add",
            "tooltip": "Afwijking +1",
            "handler": handle_plus_one,
        },
        "minus_one": {
            "icon": "remove",
            "tooltip": "Afwijking -1",
            "handler": handle_minus_one,
        },
    }


@router.page("/")
def inspectie_page() -> None:
    """Render the inspectie ronde overview page."""
    repository = create_enhanced_repository()

    # Create reactive state for changes count
    class ChangesState:
        def __init__(self):
            self.count = len(get_pending_commands())

        def update(self):
            self.count = len(get_pending_commands())

        @property
        def label(self) -> str:
            return f"Wijzigingen ({self.count})" if self.count > 0 else "Wijzigingen"

    changes_state = ChangesState()

    # Create actions for +1/-1 buttons
    row_actions = create_afwijking_actions(changes_state)

    # Add print-friendly styles with border removal
    add_print_styles(
        font_size="7px",
        orientation="portrait",
        margin="0.3in",
        remove_borders=True,
    )

    # Get current filter state for UI display
    current_filter = get_filter_state()
    filter_label = "Komende 2 weken" if current_filter == "next_two_weeks" else "Alle records"
    filter_icon = "filter_list" if current_filter == "next_two_weeks" else "view_list"

    # Render page
    with frame("Inspectie Ronde"):
        with ui.row().classes("w-full justify-between items-center mb-4"):
            ui.label("Inspectie Ronde").classes("text-h4")

            # Action buttons
            with ui.row().classes("gap-2"):
                ui.button(
                    filter_label, icon=filter_icon, on_click=toggle_filter
                ).props("outline").tooltip("Wissel tussen komende 2 weken en alle records")

                ui.button(
                    icon="edit_note", on_click=lambda: show_pending_changes_dialog(changes_state)
                ).props("outline").tooltip("Toon openstaande wijzigingen").bind_text_from(
                    changes_state, "label"
                )

                ui.button(
                    "Print", icon="print", on_click=lambda: ui.run_javascript("window.print()")
                ).props("outline").tooltip("Print de pagina")

        display_model_list_page(
            repository=repository,
            model_cls=InspectieRonde,
            table_state_key="inspectie_table",
            title="Inspectie Ronde",
            row_actions=row_actions,
        )
