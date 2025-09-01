"""Potting lots page implementation."""

import logging
from typing import Dict, Any

from nicegui import APIRouter, ui

from production_control.web.components.styles import HEADER_CLASSES

from ...potting_lots.repositories import PottingLotRepository
from ...potting_lots.models import PottingLot
from ...potting_lots.active_service import ActivePottingLotService
from ..components import frame
from ..components.model_detail_page import display_model_detail_page, create_model_view_action
from ..components.model_list_page import display_model_list_page
from ..components import potting_lot_label_printer
from ..components.barcode_scanner import create_barcode_scanner_ui
from ...potting_lots.url_parser import extract_lot_id_from_barcode


router = APIRouter(prefix="/potting-lots")
table_state_key = "potting_lots_table"
logger = logging.getLogger(__name__)

# Global service instances to maintain state across the application
# Use lazy loading to avoid initialization-time environment variable issues
_repository = None
_active_service = None


def get_repository() -> PottingLotRepository:
    """Get the repository instance, creating it lazily if needed."""
    global _repository
    if _repository is None:
        _repository = PottingLotRepository()
    return _repository


def get_active_service() -> ActivePottingLotService:
    """Get the active service instance, creating it lazily if needed."""
    global _active_service
    if _active_service is None:
        _active_service = ActivePottingLotService(get_repository())
    return _active_service


##################################################
# Lot details popup
##################################################


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
                        get_active_service(), line, lot
                    ),
                )

    # Show the standard model details
    display_model_card(lot, title=f"Oppotpartij: {lot.naam}")


##################################################
# Label printing handlers
##################################################


def create_label_action() -> Dict[str, Any]:
    return potting_lot_label_printer.create_label_action(table_state_key)


async def handle_print_all() -> None:
    await potting_lot_label_printer.print_all_labels(table_state_key)


##################################################
# Potting lot activation and completion
##################################################


def activate_lot_simple(
    active_service: ActivePottingLotService, line: int, lot: PottingLot
) -> None:
    """Simple activation function."""
    active_service.activate_lot(line=line, potting_lot_id=lot.id)
    ui.notify(f"Partij {lot.naam} geactiveerd op lijn {line}")


def deactivate_lot(active_service: ActivePottingLotService, line: int) -> None:
    active_service.deactivate_lot(line)
    ui.notify(f"Lijn {line} gedeactiveerd")


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


def active_potting_lot_buttons():
    for line in [1, 2]:
        ui.button(
            f"{line}",
            color="info",
            on_click=lambda line=line: handle_active_lot_click(line),
        ).bind_text_from(
            get_active_service(),
            "active_lots_state",
            backward=lambda state, line=line: get_activation_button_text(state, line),
        ).bind_icon_from(
            get_active_service(),
            "active_lots_state",
            backward=lambda state, line=line: "edit" if state.get(line) else "info",
        )


def handle_active_lot_click(line: int) -> None:
    """Handle click on active lot header button - navigate to details if active, show info if not."""
    ui.navigate.to(f"/potting-lots/active/{line}")


def show_completion_dialog(line: int) -> None:
    """Show modal dialog for completing a potting lot with actual pot count."""
    active_lot = get_active_service().get_active_lot_for_line(line)
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
    if get_active_service().complete_lot(line, actual_pots_int):
        ui.notify(f"Oppotten voltooid! {actual_pots_int} potten gerealiseerd", type="positive")
        dialog.close()
        # Navigate back to main page
        ui.navigate.to("/potting-lots")
    else:
        ui.notify("Fout bij voltooien van oppotten", type="negative")


def handle_deactivation(line: int) -> None:
    """Handle deactivation of the active lot on the specified line."""
    active_lot = get_active_service().get_active_lot_for_line(line)
    if active_lot:
        deactivate_lot(get_active_service(), line)
        ui.navigate.to("/potting-lots")
    else:
        ui.notify("Geen actieve partij gevonden op deze lijn")


def activate_selected_lot(line: int, selected_lot_id_str: str) -> None:
    """Activate the selected lot on the specified line."""
    if not selected_lot_id_str:
        ui.notify("Selecteer eerst een oppotpartij", type="warning")
        return

    try:
        lot_id = int(selected_lot_id_str)
        lot = get_repository().get_by_id(lot_id)
        if lot:
            get_active_service().activate_lot(line=line, potting_lot_id=lot_id)
            ui.notify(f"Partij {lot.naam} geactiveerd op lijn {line}", type="positive")
            # Navigate back to refresh the page
            ui.navigate.to(f"/potting-lots/active/{line}")
        else:
            ui.notify("Oppotpartij niet gevonden", type="negative")
    except ValueError:
        ui.notify("Ongeldige oppotpartij selectie", type="negative")


def activate_scanned_lot(line: int, barcode_text: str) -> None:
    """Activate a lot based on scanned barcode."""
    # Extract lot ID from barcode using the URL parser
    lot_id = extract_lot_id_from_barcode(barcode_text)

    if lot_id is not None:
        # Valid lot ID found
        lot = get_repository().get_by_id(lot_id)
        if lot:
            get_active_service().activate_lot(line=line, potting_lot_id=lot_id)
            ui.notify(f"Partij {lot.naam} geactiveerd op lijn {line}", type="positive")
            # Navigate back to refresh the page
            ui.navigate.to(f"/potting-lots/active/{line}")
        else:
            ui.notify(f"Oppotpartij {lot_id} niet gevonden", type="negative")
    else:
        # No valid lot ID could be extracted, try name-based search as fallback
        lots = get_repository().get_all()
        matching_lot = None

        # Try to find a lot that matches the barcode text by name
        barcode_clean = barcode_text.strip()
        for lot in lots:
            if lot.naam == barcode_clean or barcode_clean in lot.naam:
                matching_lot = lot
                break

        if matching_lot:
            get_active_service().activate_lot(line=line, potting_lot_id=matching_lot.id)
            ui.notify(f"Partij {matching_lot.naam} geactiveerd op lijn {line}", type="positive")
            ui.navigate.to(f"/potting-lots/active/{line}")
        else:
            ui.notify(f"Geen oppotpartij gevonden voor barcode: {barcode_text}", type="negative")


def generate_qr_code_for_page(line: int) -> None:
    """Generate and display QR code for the current active lot page."""
    import qrcode
    from io import BytesIO
    import base64

    # Get the current page URL - handle test environment gracefully
    try:
        base_url = getattr(ui.context.client, "base_url", "http://localhost:8080")
        page_url = f"{base_url}/potting-lots/active/{line}"
    except (AttributeError, RuntimeError):
        # Fallback for test environment or when context is not available
        page_url = f"http://localhost:8080/potting-lots/active/{line}"

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=6,
        border=4,
    )
    qr.add_data(page_url)
    qr.make(fit=True)

    # Create QR code image
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Convert to base64 for display
    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.read()).decode()

    # Display the QR code
    with ui.row().classes("justify-center"):
        ui.image(f"data:image/png;base64,{img_base64}").classes("w-48 h-48")

    ui.label(f"URL: {page_url}").classes("text-sm text-gray-600")


##################################################
# Pages
##################################################


# Potting index
@router.page("/")
def potting_lots_page() -> None:

    row_actions = {
        "view": create_model_view_action(
            repository=get_repository(),
            custom_display_function=custom_display,
        ),
        "label": create_label_action(),
    }

    with frame("Oppotlijst"):

        with ui.row().classes("w-full justify-between items-center mb-4"):
            # Active potting lots and print button
            with ui.row().classes("gap-2"):
                active_potting_lot_buttons()

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
            repository=get_repository(),
            model_cls=PottingLot,
            table_state_key=table_state_key,
            title="Oppotlijst",
            row_actions=row_actions,
        )


# Potting lot details
@router.page("/{id}")
def potting_lot_detail(id: int) -> None:
    record = get_repository().get_by_id(id)

    with frame("Oppotlijst Details"):
        display_model_detail_page(
            model=record,
            title="Oppotlijst Details",
            back_link_text="← Terug naar Oppotlijst",
            back_link_url="/potting-lots",
            custom_display_function=custom_display,
        )


# Active potting requests by line
@router.page("/active/{line}")
def active_lot_details(line: int) -> None:
    """Show details page for the currently active lot on the specified line."""
    active_lot = get_active_service().get_active_lot_for_line(line)

    if not active_lot:
        title = f"Lijn {line} - Geen Actieve Partij"
        with frame(title):
            top_lots = get_repository().get_top_lots(50)
            lot_options = {str(lot.id): f"{lot.id}: {lot.naam}" for lot in top_lots}

            with ui.column().classes("w-full gap-4"):
                ui.label(title).classes(HEADER_CLASSES)
                # Dropdown selection and activation
                with ui.card().classes("w-full"):
                    ui.label("Selecteer een oppotpartij om te activeren:").classes("font-semibold")

                    selected_lot_id = ui.select(
                        options=lot_options, label="Oppotpartij", with_input=True
                    ).classes("w-full")

                    ui.button(
                        "Activeren op deze lijn",
                        color="positive",
                        icon="play_arrow",
                        on_click=lambda: activate_selected_lot(line, selected_lot_id.value),
                    ).classes("mt-2")

                # Barcode scanner for lot activation
                with ui.card().classes("w-full"):
                    ui.label("Scan Oppotpartij Label:").classes("font-semibold")
                    create_barcode_scanner_ui(
                        on_scan=lambda barcode: activate_scanned_lot(line, barcode)
                    )

                # QR Code for mobile access
                with ui.card().classes("w-full"):
                    ui.label("Scan QR-code om deze pagina op je telefoon te openen:").classes(
                        "font-semibold"
                    )
                    generate_qr_code_for_page(line)
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


@router.page("/scan/{id}")
def potting_lot_scan(id: int) -> None:
    ui.navigate.to(router.url_path_for("potting_lot_detail", id=id))
