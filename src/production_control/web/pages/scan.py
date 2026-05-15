"""Mobile-optimized barcode scanning page for viewing batch information."""

import logging

from nicegui import APIRouter, ui

from ...potting_lots.models import PottingLot
from ...potting_lots.repositories import PottingLotRepository
from ...potting_lots.url_parser import extract_lot_id_from_barcode
from ..components.barcode_scanner import create_barcode_scanner_ui
from ..components import frame

logger = logging.getLogger(__name__)

# Router for scan pages
router = APIRouter(prefix="/scan")


def get_repository() -> PottingLotRepository:
    """Get the potting lot repository instance."""
    return PottingLotRepository()


@router.page("")
def scan_page(autostart: bool = False) -> None:
    """Mobile-optimized scanning page for viewing batch information."""
    with frame("Scan"):
        with ui.column().classes("w-full max-w-2xl mx-auto p-4 gap-4"):
            # Scanner card
            with ui.card().classes("w-full"):
                create_barcode_scanner_ui(
                    on_scan=lambda barcode: handle_scan(barcode), autostart=autostart
                )


def handle_scan(barcode: str) -> None:
    """Handle scanned barcode and display batch information."""
    logger.info(f"Handling scanned barcode: {barcode}")

    # Extract lot ID from scanned barcode
    lot_id = extract_lot_id_from_barcode(barcode)

    if lot_id is None:
        ui.notify("Invalid QR code format", type="negative")
        logger.warning(f"Could not extract lot ID from barcode: {barcode}")
        return

    # Look up the potting lot
    try:
        lot = get_repository().get_by_id(lot_id)
        if lot is None:
            ui.notify(f"Batch {lot_id} not found", type="negative")
            logger.warning(f"Potting lot not found: {lot_id}")
            return

        # Display the batch information
        display_batch_info(lot)
        ui.notify("Batch loaded successfully", type="positive")

    except Exception as e:
        ui.notify(f"Error loading batch: {str(e)}", type="negative")
        logger.error(f"Error loading potting lot {lot_id}: {e}", exc_info=True)


def display_batch_info(lot: PottingLot) -> None:
    """Display batch information in a mobile-optimized format."""
    # Navigate to mobile-optimized view page
    ui.navigate.to(f"/scan/view/{lot.id}")


def col_for_field(label, value):
    lbl_style = "text-xs text-gray-600 uppercase"
    val_style = "text-sm font-medium"
    with ui.column().classes("gap-1"):
        ui.label(label).classes(lbl_style)
        ui.label(str(value)).classes(val_style)


def card_for_fields(kv):
    with ui.card().classes("w-full p-4"):
        with ui.grid(columns=3).classes("w-full gap-3"):
            for k, v in kv.items():
                col_for_field(k, v)


@router.page("/view/{id}")
def view_batch(id: int) -> None:
    """Mobile-optimized view of batch information."""
    try:
        lot = get_repository().get_by_id(id)

        if lot is None:
            with frame("Batch Not Found"):
                with ui.column().classes("w-full max-w-2xl mx-auto p-4 gap-4"):
                    ui.label("Batch Not Found").classes("text-2xl font-bold text-red-600")
                    ui.label(f"Batch {id} could not be found").classes("text-gray-600 mb-4")
                    ui.button("Scan Another", on_click=lambda: ui.navigate.to("/scan")).props(
                        "icon=qr_code_scanner"
                    ).classes("w-full")
            return

        title = f"{lot.product_groep} · {lot.naam} · {lot.id} · {lot.oppot_week}"
        # Display batch information in mobile-optimized format
        with frame(title):
            with ui.column().classes("w-full max-w-2xl mx-auto p-4 gap-4"):
                ui.label(title).classes("text-lg font-semibold mb-3")

                card_for_fields(
                    {
                        "Bolmaat": lot.bolmaat,
                        "Certificaat": lot.cert_nr,
                        "Code": lot.bollen_code,
                    }
                )

                card_for_fields(
                    {
                        "Oppotweek": lot.oppot_week,
                        "Oppotdatum": lot.oppot_datum,
                        "Stuks": lot.aantal_pot,
                    }
                )

                with ui.card().classes("w-full p-4"):
                    with ui.grid(columns=3).classes("w-full gap-3"):
                        col_for_field("Klantcode", lot.klant_code)
                        col_for_field("Afleverdatum", "-")
                        # add column here with inspectieronde actions (+, -, view)

                # Remarks section (if exists)
                if lot.opmerking:
                    with ui.card().classes("w-full p-4"):
                        ui.label("Opmerkingen").classes("text-sm text-gray-600 uppercase mb-2")
                        ui.label(lot.opmerking).classes("text-sm")

                # Action buttons
                with ui.row().classes("w-full gap-2 mt-4"):
                    ui.button("Scan Another", on_click=lambda: ui.navigate.to("/scan")).props(
                        "icon=qr_code_scanner"
                    ).classes("flex-1")
                    ui.button(
                        "View Details",
                        on_click=lambda: ui.navigate.to(f"/potting-lots/{id}"),
                    ).props("icon=info outline").classes("flex-1")

    except Exception as e:
        logger.error(f"Error displaying batch {id}: {e}", exc_info=True)
        with frame("Error"):
            with ui.column().classes("w-full max-w-2xl mx-auto p-4 gap-4"):
                ui.label("Error Loading Batch").classes("text-2xl font-bold text-red-600")
                ui.label(f"An error occurred: {str(e)}").classes("text-gray-600 mb-4")
                ui.button("Scan Another", on_click=lambda: ui.navigate.to("/scan")).props(
                    "icon=qr_code_scanner"
                ).classes("w-full")
