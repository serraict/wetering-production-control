"""Potting lots page implementation."""

import logging
from typing import Dict, Any
from datetime import date

from nicegui import APIRouter, ui, run

from ...potting_lots.repositories import PottingLotRepository
from ...potting_lots.models import PottingLot
from ...potting_lots.label_generation import LabelGenerator
from ...potting_lots.active_service import ActivePottingLotService
from ...potting_lots.line_controller import get_controller
from ..components import frame
from ..components.model_detail_page import display_model_detail_page, create_model_view_action
from ..components.model_list_page import display_model_list_page
from ..components.table_state import ClientStorageTableState


router = APIRouter(prefix="/potting-lots")
label_generator = LabelGenerator()
table_state_key = "potting_lots_table"
logger = logging.getLogger(__name__)

# Global service instances to maintain state across the application
_repository = PottingLotRepository()
_active_service = ActivePottingLotService(_repository)
_line_controller = get_controller()


def create_label_action() -> Dict[str, Any]:

    async def handle_label(e: Dict[str, Any]) -> None:
        id_value = e.args.get("key")
        table_state = ClientStorageTableState.initialize(table_state_key)
        record = next(
            (PottingLot(**row) for row in table_state.rows if row["id"] == id_value), None
        )

        if record:
            # Create a descriptive filename, this is used for the downloaded file for the user
            filename = f"oppotpartij_{record.id}_{record.naam.replace(' ', '_')}.pdf"
            ui.notify("Generating label...")

            try:
                pdf_path = await run.cpu_bound(generate_labels, record)
                ui.download(pdf_path, filename=filename)
                label_generator.cleanup_pdf(pdf_path)
            except Exception as e:
                msg = f"Error generating label: {str(e)}"
                print(msg)
                ui.notify(msg)

    return {
        "icon": "print",
        "tooltip": "Druk 2 labels af voor deze partij",
        "handler": handle_label,
    }


def generate_labels(records, filename=None) -> str:
    """Generate PDF labels for records in a background process.

    Args:
        records: List of PottingLot records
        filename: Optional name for the output file

    Returns:
        Path to the generated PDF file
    """
    label_generator = LabelGenerator()
    return label_generator.generate_pdf(records)


async def handle_print_all() -> None:
    table_state = ClientStorageTableState.initialize(table_state_key)

    records = [PottingLot(**visible_row) for visible_row in table_state.rows]

    if not records:
        return

    ui.notify("Generating labels...")

    try:
        # Generate labels in background process
        pdf_path = await run.cpu_bound(generate_labels, records)

        # Download and cleanup
        filename = f"oppotpartijen_{date.today():%gW%V-%u}.pdf"
        ui.download(pdf_path, filename=filename)
        label_generator.cleanup_pdf(pdf_path)

    except Exception as e:
        msg = f"Error generating labels: {str(e)}"
        print(msg)
        ui.notify(msg)


def custom_display(lot: PottingLot) -> None:
    """Custom display for potting lot detail with activation button."""
    from ..components.model_card import display_model_card

    # Show activation status and button
    with ui.row().classes("w-full justify-between items-center mb-4"):
        for line in [1, 2]:
            with ui.row().classes("gap-2"):
                ui.button(
                    f"Activeren op Lijn {line}",
                    icon="play_arrow",
                    color="positive",
                    on_click=lambda line=line, lot=lot: activate_lot_simple(
                        _active_service, line, lot
                    ),
                )

    # Show the standard model details
    display_model_card(lot, title=f"Oppotpartij: {lot.naam}")


def activate_lot_simple(
    active_service: ActivePottingLotService, line: int, lot: PottingLot
) -> None:
    """Simple activation function."""
    active_service.activate_lot(line=line, potting_lot_id=lot.id)
    ui.notify(f"Partij {lot.naam} geactiveerd op lijn {line}")


def get_activation_status_text(active_lots_state: dict, line: int) -> str:
    """Helper function to get activation status text for a line."""
    active_lot = active_lots_state.get(line)
    return active_lot.potting_lot.naam if active_lot else "--"


def get_activation_button_text(active_lots_state: dict, line: int) -> str:
    """Helper function to get activation button text for a line."""
    active_lot = active_lots_state.get(line)
    return f"{line}: {active_lot.potting_lot.naam if active_lot else '--'}"


def get_tool_tip_text(active_lots_state: dict, line: int) -> str:
    """Helper function to get tooltip text for a line showing name and id of the active lot."""
    active_lot = active_lots_state.get(line)
    if active_lot:
        lot = active_lot.potting_lot
        return f"{lot.id}: {lot.naam}"
    return "Geen actieve partij"


def deactivate_lot(active_service: ActivePottingLotService, line: int) -> None:
    _active_service.deactivate_lot(line)
    ui.notify(f"Lijn {line} gedeactiveerd")


@router.page("/")
async def potting_lots_page() -> None:

    row_actions = {
        "view": create_model_view_action(
            repository=_repository,
            custom_display_function=custom_display,
        ),
        "label": create_label_action(),
    }

    with frame("Oppotlijst"):

        with ui.row().classes("w-full justify-between items-center mb-4"):
            # Active potting lots and print button
            with ui.row().classes("gap-2"):
                # Display active potting lots:
                for line in [1, 2]:
                    ui.button(
                        f"{line}",
                        color="info",
                        on_click=lambda line=line: handle_active_lot_click(line),
                    ).bind_text_from(
                        _active_service,
                        "active_lots_state",
                        backward=lambda state, line=line: get_activation_button_text(state, line),
                    ).bind_icon_from(
                        _active_service,
                        "active_lots_state",
                        backward=lambda state, line=line: "edit" if state.get(line) else "info",
                    )

            # print button
            print_all_caption = "Labels Afdrukken"
            print_all_icon = "print"
            with ui.button(print_all_caption, icon=print_all_icon).classes(
                "bg-primary"
            ) as print_all_button:
                ui.tooltip("Druk labels af voor alle zichtbare regels")

                async def handle_print_with_feedback():
                    print_all_button.disable()
                    print_all_button.icon = "hourglass_top"
                    try:
                        await handle_print_all()
                    finally:
                        print_all_button.text = print_all_caption
                        print_all_button.icon = print_all_icon
                        print_all_button.enable()

                print_all_button.on_click(handle_print_with_feedback)

        display_model_list_page(
            repository=_repository,
            model_cls=PottingLot,
            table_state_key=table_state_key,
            title="Oppotlijst",
            row_actions=row_actions,
        )


@router.page("/{id}")
def potting_lot_detail(id: int) -> None:
    record = _repository.get_by_id(id)

    with frame("Oppotlijst Details"):
        display_model_detail_page(
            model=record,
            title="Oppotlijst Details",
            back_link_text="← Terug naar Oppotlijst",
            back_link_url="/potting-lots",
            custom_display_function=custom_display,
        )


@router.page("/active/{line}")
def active_lot_details(line: int) -> None:
    """Show details page for the currently active lot on the specified line."""
    active_lot = _active_service.get_active_lot_for_line(line)

    if not active_lot:
        with frame(f"Lijn {line} - Geen Actieve Partij"):
            ui.label("Er is momenteel geen actieve partij op deze lijn.")
            ui.button("← Terug naar Oppotlijst", on_click=lambda: ui.navigate.to("/potting-lots"))
        return

    with frame(f"Lijn {line} - Actieve Partij: {active_lot.potting_lot.naam}"):
        from ..components.model_card import display_model_card

        # Action buttons at top right
        with ui.row().classes("w-full justify-end mb-4 gap-2"):
            ui.button(
                "Oppotten Voltooid", color="positive", on_click=lambda: show_completion_dialog(line)
            ).props("icon=check_circle")
            ui.button(
                "Deactiveren", color="negative", on_click=lambda: handle_deactivation(line)
            ).props("icon=stop")

        # Display lot details using standard model card
        display_model_card(active_lot.potting_lot, title=f"Actieve Oppotpartij - Lijn {line}")


def handle_deactivation(line: int) -> None:
    """Handle deactivation of the active lot on the specified line."""
    active_lot = _active_service.get_active_lot_for_line(line)
    if active_lot:
        deactivate_lot(_active_service, line)
        ui.navigate.to("/potting-lots")
    else:
        ui.notify("Geen actieve partij gevonden op deze lijn")


def handle_active_lot_click(line: int) -> None:
    """Handle click on active lot header button - navigate to details if active, show info if not."""
    active_lot = _active_service.get_active_lot_for_line(line)
    if active_lot:
        # Navigate to active lot details page
        ui.navigate.to(f"/potting-lots/active/{line}")
    else:
        # Show info about no active lot
        ui.notify(f"Geen actieve partij op lijn {line}")


def show_completion_dialog(line: int) -> None:
    """Show modal dialog for completing a potting lot with actual pot count."""
    active_lot = _active_service.get_active_lot_for_line(line)
    if not active_lot:
        ui.notify("Geen actieve partij gevonden op deze lijn")
        return

    with ui.dialog() as dialog, ui.card():
        ui.label(f"Oppotten Voltooid - {active_lot.potting_lot.naam}").classes(
            "text-xl font-bold mb-4"
        )

        with ui.row():
            actual_pots_input = ui.number(
                "Aantal", placeholder="Voer aantal potten in", min=1, step=1, format="%.0f"
            ).classes("w-40")

        with ui.row().classes("gap-2 justify-end"):
            ui.button("Annuleren", on_click=dialog.close)
            ui.button(
                "Voltooid",
                color="positive",
                icon="check",
                on_click=lambda: handle_completion(line, actual_pots_input.value, dialog),
            )

    dialog.open()


def handle_completion(line: int, actual_pots: float, dialog) -> None:
    """Handle the completion of a potting lot."""
    if actual_pots is None or actual_pots <= 0:
        ui.notify("Voer een geldig aantal potten in", type="negative")
        return

    # Convert to integer
    actual_pots_int = int(actual_pots)

    # Complete the lot using the service
    if _active_service.complete_lot(line, actual_pots_int):
        ui.notify(f"Oppotten voltooid! {actual_pots_int} potten gerealiseerd", type="positive")
        dialog.close()
        # Navigate back to main page
        ui.navigate.to("/potting-lots")
    else:
        ui.notify("Fout bij voltooien van oppotten", type="negative")


@router.page("/scan/{id}")
def potting_lot_scan(id: int) -> None:
    ui.navigate.to(router.url_path_for("potting_lot_detail", id=id))
