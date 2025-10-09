"""Inspectie page implementation."""

import os
from typing import Dict, Any, List
import httpx

from nicegui import APIRouter, ui, app

from ...inspectie.repositories import InspectieRepository
from ...inspectie.models import InspectieRonde
from ...inspectie.commands import UpdateAfwijkingCommand
from ..components import frame
from ..components.model_list_page import display_model_list_page
from ..components.model_detail_page import create_model_view_action
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
    for code, change_data in storage["inspectie_changes"].items():
        if isinstance(change_data, dict):
            # New format with original and new values
            new_afwijking = change_data["new"]
        else:
            # Legacy format (fallback)
            new_afwijking = change_data

        commands.append(UpdateAfwijkingCommand(code=code, new_afwijking=new_afwijking))

    return commands


def clear_pending_commands() -> None:
    """Clear all pending commands from browser storage."""
    storage = get_storage()
    if "inspectie_changes" in storage:
        del storage["inspectie_changes"]


async def commit_pending_commands() -> Dict[str, Any]:
    """Commit all pending commands to Firebird database.

    Returns:
        Dict with success status and message
    """
    commands = get_pending_commands()

    if not commands:
        return {"success": False, "message": "Geen openstaande wijzigingen"}

    errors = []
    success_count = 0

    # Use the NiceGUI app's base URL (same server as the web interface)
    # This works for both development and production without configuration
    port = int(os.getenv("NICEGUI_PORT", "8080"))
    api_base_url = f"http://localhost:{port}"
    api_url = "/api/firebird/update-afwijking"

    async with httpx.AsyncClient(base_url=api_base_url) as client:
        for command in commands:
            try:
                response = await client.post(
                    api_url,
                    json={"code": command.code, "new_afwijking": command.new_afwijking},
                    timeout=10.0,
                )

                if response.status_code == 200:
                    success_count += 1
                else:
                    errors.append(f"{command.code}: {response.text}")
            except Exception as e:
                errors.append(f"{command.code}: {str(e)}")

    if errors:
        return {
            "success": False,
            "message": f"{success_count} succesvol, {len(errors)} fouten: {'; '.join(errors[:3])}",
        }
    else:
        # Clear commands on success
        clear_pending_commands()
        return {"success": True, "message": f"{success_count} wijzigingen opgeslagen in database"}


def get_filter_state() -> str:
    """Get current filter state from browser storage."""
    storage = get_storage()
    return storage.get("inspectie_filter", "next_two_weeks")


def set_filter_state(filter_state: str) -> None:
    """Set filter state in browser storage."""
    storage = get_storage()
    storage["inspectie_filter"] = filter_state


def get_compact_view_state() -> bool:
    """Get current compact view state from browser storage."""
    storage = get_storage()
    return storage.get("inspectie_compact_view", False)


def set_compact_view_state(compact_view: bool) -> None:
    """Set compact view state in browser storage."""
    storage = get_storage()
    storage["inspectie_compact_view"] = compact_view


def toggle_compact_view() -> None:
    """Toggle compact view state."""
    current_state = get_compact_view_state()
    set_compact_view_state(not current_state)

    # Refresh the page to apply the new view
    ui.run_javascript("location.reload()")


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

            rows = []
            for code, change_data in changes.items():
                if isinstance(change_data, dict):
                    # New format: show the difference from original
                    original = change_data["original"] or 0
                    new_value = change_data["new"]
                    difference = new_value - original
                    rows.append(
                        {"code": code, "change": f"{original} → {new_value} ({difference:+d})"}
                    )
                else:
                    # Legacy format
                    rows.append({"code": code, "change": f"{change_data:+d}"})

            ui.table(columns=columns, rows=rows, row_key="code").classes(
                "w-full print-preserve-columns"
            )

            ui.separator().classes("my-4")

            # Action buttons
            with ui.row().classes("w-full justify-between"):
                ui.button(
                    "Alles wissen",
                    icon="clear_all",
                    color="negative",
                    on_click=lambda: handle_clear_all_changes_and_close(dialog, changes_state),
                ).props("outline")

                ui.button(
                    "Alles opslaan",
                    icon="save",
                    color="positive",
                    on_click=lambda: handle_commit_changes(dialog, changes_state),
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


async def handle_commit_changes(dialog, changes_state=None) -> None:
    """Handle committing all changes to Firebird database."""
    result = await commit_pending_commands()

    if result["success"]:
        ui.notify(result["message"], type="positive")
        if changes_state:
            changes_state.update()
        dialog.close()
    else:
        ui.notify(result["message"], type="negative")


def create_afwijking_actions(repository: InspectieRepository, changes_state=None) -> Dict[str, Any]:
    """Create row actions for +1/-1 buttons and view details."""

    def handle_plus_one(e: Dict[str, Any]) -> None:
        """Handle +1 button click."""
        code = e.args.get("key")
        if not code:
            ui.notify("Geen code gevonden", type="negative")
            return

        # Get the current afwijking from the row data
        row_data = e.args.get("row", {})
        current_afwijking = row_data.get("afwijking_afleveren", 0) or 0

        # Get storage safely
        storage = get_storage()

        # Initialize storage if needed
        if "inspectie_changes" not in storage:
            storage["inspectie_changes"] = {}

        # Check if this is the first change for this code
        if code not in storage["inspectie_changes"]:
            # First change: store both original and new value
            new_afwijking = current_afwijking + 1
            storage["inspectie_changes"][code] = {
                "original": current_afwijking,
                "new": new_afwijking,
            }
        else:
            # Subsequent change: increment the new value
            change_data = storage["inspectie_changes"][code]
            if isinstance(change_data, dict):
                new_afwijking = change_data["new"] + 1
                storage["inspectie_changes"][code]["new"] = new_afwijking
            else:
                # Handle legacy format (just in case)
                new_afwijking = current_afwijking + 1
                storage["inspectie_changes"][code] = {
                    "original": current_afwijking,
                    "new": new_afwijking,
                }

        # Create and store command
        command = UpdateAfwijkingCommand(code=code, new_afwijking=new_afwijking)

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

        # Get the current afwijking from the row data
        row_data = e.args.get("row", {})
        current_afwijking = row_data.get("afwijking_afleveren", 0) or 0

        # Get storage safely
        storage = get_storage()

        # Initialize storage if needed
        if "inspectie_changes" not in storage:
            storage["inspectie_changes"] = {}

        # Check if this is the first change for this code
        if code not in storage["inspectie_changes"]:
            # First change: store both original and new value
            new_afwijking = current_afwijking - 1
            storage["inspectie_changes"][code] = {
                "original": current_afwijking,
                "new": new_afwijking,
            }
        else:
            # Subsequent change: decrement the new value
            change_data = storage["inspectie_changes"][code]
            if isinstance(change_data, dict):
                new_afwijking = change_data["new"] - 1
                storage["inspectie_changes"][code]["new"] = new_afwijking
            else:
                # Handle legacy format (just in case)
                new_afwijking = current_afwijking - 1
                storage["inspectie_changes"][code] = {
                    "original": current_afwijking,
                    "new": new_afwijking,
                }

        # Create and store command
        command = UpdateAfwijkingCommand(code=code, new_afwijking=new_afwijking)

        ui.notify(f"Afwijking -1 voor {code} (totaal: {command.new_afwijking})", type="positive")

        # Update changes state if provided
        if changes_state:
            changes_state.update()

    # Create view action for showing all details
    view_action = create_model_view_action(
        repository=repository,
        id_field="code",
        dialog=True,
    )

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
        "view": {
            "icon": "visibility",
            "tooltip": "Bekijk details",
            "handler": view_action["handler"],
        },
    }


@router.page("/")
def inspectie_page() -> None:
    """Render the inspectieronde overview page."""
    repository = create_enhanced_repository()

    # Create reactive state for changes count
    class ChangesState:
        def __init__(self):
            self.count = len(get_pending_commands())
            self.refresh_callback = None

        def update(self):
            self.count = len(get_pending_commands())
            if self.refresh_callback:
                self.refresh_callback()

        def set_refresh_callback(self, callback):
            """Set a callback to be called when state is updated."""
            self.refresh_callback = callback

        @property
        def badge(self) -> str:
            """Return badge text showing count."""
            return str(self.count) if self.count > 0 else ""

    changes_state = ChangesState()

    # Create actions for +1/-1 buttons and view details
    row_actions = create_afwijking_actions(repository, changes_state)

    # Add print-friendly styles with border removal
    add_print_styles(
        font_size="7px",
        orientation="portrait",
        margin="0.3in",
        remove_borders=True,
    )

    # Get current filter state for UI display
    current_filter = get_filter_state()
    filter_icon = "filter_list" if current_filter == "next_two_weeks" else "view_list"
    filter_tooltip = (
        "3 weken periode - klik om alle records te tonen"
        if current_filter == "next_two_weeks"
        else "Alle records - klik om 3 weken periode te tonen"
    )

    # Get current compact view state for UI display
    compact_view = get_compact_view_state()
    view_icon = "view_agenda" if compact_view else "view_list"
    view_tooltip = (
        "Compacte weergave - klik voor volledige weergave"
        if compact_view
        else "Volledige weergave - klik voor compacte weergave"
    )

    # Render page
    with frame("Inspectieronde"):
        with ui.row().classes("w-full justify-between items-center mb-4"):
            ui.label("Inspectieronde").classes("text-h4")

            # Action buttons
            with ui.row().classes("gap-2"):
                ui.button(icon=filter_icon, on_click=toggle_filter).props("outline").tooltip(
                    filter_tooltip
                ).props("aria-label='Filter weergave'")

                ui.button(icon=view_icon, on_click=toggle_compact_view).props("outline").tooltip(
                    view_tooltip
                ).props("aria-label='Wissel weergave'")

                changes_button = ui.button(
                    icon="edit_note", on_click=lambda: show_pending_changes_dialog(changes_state)
                ).props("outline")
                changes_button.tooltip("Openstaande wijzigingen")
                # Bind button text to show count
                changes_button.bind_text_from(changes_state, "badge")

                ui.button(icon="print", on_click=lambda: ui.run_javascript("window.print()")).props(
                    "outline"
                ).tooltip("Print de pagina").props("aria-label='Print'")

        if compact_view:
            # Card view for compact mode
            from ..components.table_state import ClientStorageTableState
            from ..components.table_utils import format_row

            table_state = ClientStorageTableState.initialize("inspectie_table")

            def load_data():
                pagination = table_state.pagination
                filter_text = table_state.filter
                items, total = repository.get_paginated(
                    pagination=pagination,
                    filter_text=filter_text,
                )
                table_state.update_rows([format_row(item) for item in items], total)
                render_cards.refresh()
                render_pagination.refresh()

            @ui.refreshable
            def render_cards():
                storage = get_storage()
                changes = storage.get("inspectie_changes", {})

                with ui.row().classes("w-full gap-4 flex-wrap"):
                    for item in table_state.rows:
                        code = item.get("id")
                        has_pending_change = code in changes
                        card_classes = "w-full sm:w-80"
                        if has_pending_change:
                            card_classes += " border-l-4"

                        with (
                            ui.card()
                            .classes(card_classes)
                            .style("border-left-color: #f39c21" if has_pending_change else None)
                        ):
                            with ui.row().classes("w-full justify-between items-center"):
                                ui.label(item.get("product_naam", "")).classes("text-lg font-bold")
                                ui.label(item.get("datum_afleveren_plan", "")).classes(
                                    "text-sm text-gray-600"
                                )

                            with ui.row().classes("w-full gap-2 mt-2"):
                                ui.label("Baan:").classes("text-sm font-semibold")
                                ui.label(item.get("baan_samenvatting", "")).classes("text-sm")

                            with ui.row().classes("w-full gap-2"):
                                ui.label("Afwijking:").classes("text-sm font-semibold")
                                current_afwijking = item.get("afwijking_afleveren") or 0

                                if has_pending_change:
                                    change_data = changes[code]
                                    if isinstance(change_data, dict):
                                        new_value = change_data["new"]
                                        ui.label(f"{current_afwijking} → {new_value}").classes(
                                            "text-base font-bold text-accent"
                                        )
                                    else:
                                        ui.label(f"{current_afwijking} ({change_data:+d})").classes(
                                            "text-base font-bold text-accent"
                                        )
                                else:
                                    ui.label(str(current_afwijking)).classes("text-sm")

                            # Action buttons
                            with ui.row().classes("w-full justify-end gap-2 mt-2"):
                                ui.button(
                                    icon="add",
                                    on_click=lambda _e, code=item.get("id"), row=item: row_actions[
                                        "plus_one"
                                    ]["handler"](
                                        type("Event", (), {"args": {"key": code, "row": row}})()
                                    ),
                                ).props("dense flat color=primary").tooltip("+1")

                                ui.button(
                                    icon="remove",
                                    on_click=lambda _e, code=item.get("id"), row=item: row_actions[
                                        "minus_one"
                                    ]["handler"](
                                        type("Event", (), {"args": {"key": code, "row": row}})()
                                    ),
                                ).props("dense flat color=primary").tooltip("-1")

                                ui.button(
                                    icon="visibility",
                                    on_click=lambda _e, code=item.get("id"), row=item: row_actions[
                                        "view"
                                    ]["handler"](
                                        type("Event", (), {"args": {"key": code, "row": row}})()
                                    ),
                                ).props("dense flat color=primary").tooltip("Details")

            @ui.refreshable
            def render_pagination():
                # Calculate total pages (handle 0 = show all)
                rows_per_page = table_state.pagination.rows_per_page
                if rows_per_page == 0:
                    total_pages = 1  # All rows on one page
                else:
                    total_pages = (
                        table_state.pagination.total_rows + rows_per_page - 1
                    ) // rows_per_page

                # Show pagination controls
                with ui.row().classes("w-full justify-between items-center mt-4"):
                    # Page size selector on left
                    with ui.row().classes("items-center gap-2"):
                        ui.label("Rijen per pagina:")
                        # Create options with labels - show "Alle" instead of 0
                        options_dict = {
                            10: "10",
                            25: "25",
                            50: "50",
                            0: f"Alle ({table_state.pagination.total_rows})",
                        }
                        ui.select(
                            options=options_dict,
                            value=table_state.pagination.rows_per_page,
                            on_change=lambda e: (
                                setattr(table_state.pagination, "rows_per_page", e.value),
                                setattr(table_state.pagination, "page", 1),
                                load_data(),
                            ),
                        ).props("dense options-dense").classes("w-32").bind_value(
                            table_state.pagination, "rows_per_page"
                        )

                    # Page navigation on right (only if more than one page)
                    if total_pages > 1:
                        with ui.row().classes("items-center gap-2"):
                            # Previous button
                            ui.button(
                                icon="chevron_left",
                                on_click=lambda: (
                                    setattr(
                                        table_state.pagination,
                                        "page",
                                        table_state.pagination.page - 1,
                                    ),
                                    load_data(),
                                ),
                            ).props("flat round").bind_enabled_from(
                                table_state.pagination, "page", backward=lambda p: p > 1
                            )

                            # Page info
                            ui.label().bind_text_from(
                                table_state.pagination,
                                "page",
                                backward=lambda p: f"Pagina {p} van {total_pages}",
                            )

                            # Next button
                            ui.button(
                                icon="chevron_right",
                                on_click=lambda: (
                                    setattr(
                                        table_state.pagination,
                                        "page",
                                        table_state.pagination.page + 1,
                                    ),
                                    load_data(),
                                ),
                            ).props("flat round").bind_enabled_from(
                                table_state.pagination, "page", backward=lambda p: p < total_pages
                            )

            # Set up refresh callback so changes trigger card refresh
            changes_state.set_refresh_callback(render_cards.refresh)

            render_cards()
            render_pagination()
            load_data()
        else:
            # Table view for full mode
            display_model_list_page(
                repository=repository,
                model_cls=InspectieRonde,
                table_state_key="inspectie_table",
                title="Inspectieronde",
                row_actions=row_actions,
                enable_fullscreen=True,
                columns=None,
            )
