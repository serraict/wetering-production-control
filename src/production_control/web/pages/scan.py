"""Mobile-optimized barcode scanning page for viewing batch information."""

import logging

from nicegui import APIRouter, ui

from ...inspectie.changes import (
    STORAGE_KEY,
    apply_delta,
    get_pending_change,
    parse_date,
)
from ...inspectie.models import InspectieRonde
from ...inspectie.repositories import InspectieRepository
from ...potting_lots.models import PottingLot
from ...potting_lots.repositories import PottingLotRepository
from ...potting_lots.url_parser import extract_lot_id_from_barcode
from ..components.barcode_scanner import create_barcode_scanner_ui
from ..components import frame
from ..components.table_utils import format_date
from .inspectie import display_inspectie_with_qr_button, get_storage

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


LBL_STYLE = "text-xs text-gray-600 uppercase"
VAL_STYLE = "text-sm font-medium"
VAL_STYLE_DIRTY = "text-sm font-medium text-accent"


def col_for_field(label, value):
    with ui.column().classes("gap-1"):
        ui.label(label).classes(LBL_STYLE)
        ui.label(str(value)).classes(VAL_STYLE)


def card_for_fields(kv):
    with ui.card().classes("w-full p-4"):
        with ui.grid(columns=3).classes("w-full gap-3"):
            for k, v in kv.items():
                col_for_field(k, v)


def _open_inspectie_detail(inspectie: InspectieRonde) -> None:
    """Show the full InspectieRonde detail in a modal dialog."""
    fresh = InspectieRepository().get_by_id(inspectie.code) or inspectie
    with ui.dialog() as dialog, ui.card():
        display_inspectie_with_qr_button(fresh)
        ui.button("Sluiten", on_click=dialog.close)
    dialog.open()


def render_klant_afleverdatum_card(lot: PottingLot, inspectie: InspectieRonde | None) -> None:
    """Render the Klantcode / Afleverdatum / Acties card.

    When there is no matching InspectieRonde the action column is omitted
    and the date shows '-'.
    """
    @ui.refreshable
    def card() -> None:
        storage = get_storage()
        with ui.card().classes("w-full p-4"):
            with ui.grid(columns=3).classes("w-full gap-3"):
                col_for_field("Klantcode", lot.klant_code or "-")

                with ui.column().classes("gap-1"):
                    ui.label("Afleverdatum").classes(LBL_STYLE)
                    if inspectie is None or inspectie.datum_afleveren_plan is None:
                        ui.label("--").classes(VAL_STYLE)
                    else:
                        original = inspectie.datum_afleveren_plan
                        change = get_pending_change(storage, inspectie.code)
                        if change:
                            new_datum = parse_date(change.get("new_datum")) or original
                            ui.label(
                                f"{format_date(original)} → {format_date(new_datum)}"
                            ).classes(VAL_STYLE_DIRTY)
                        else:
                            ui.label(format_date(original)).classes(VAL_STYLE)

                if inspectie is not None and inspectie.datum_afleveren_plan is not None:
                    with ui.column().classes("gap-1"):
                        ui.label("Acties").classes(LBL_STYLE)
                        with ui.row().classes("items-center gap-1"):

                            def on_delta(delta: int) -> None:
                                base_afwijking = inspectie.afwijking_afleveren or 0
                                new_afw, _ = apply_delta(
                                    get_storage(),
                                    inspectie.code,
                                    base_afwijking,
                                    inspectie.datum_afleveren_plan,
                                    delta,
                                )
                                ui.notify(
                                    f"Afwijking {delta:+d} voor {inspectie.code} "
                                    f"(totaal: {new_afw})",
                                    type="positive",
                                )
                                card.refresh()

                            ui.button(icon="remove", on_click=lambda: on_delta(-1)).props(
                                "dense flat color=primary"
                            ).tooltip("Eerder afleveren (-1 dag)")
                            ui.button(icon="add", on_click=lambda: on_delta(1)).props(
                                "dense flat color=primary"
                            ).tooltip("Later afleveren (+1 dag)")
                            ui.button(
                                icon="visibility",
                                on_click=lambda: _open_inspectie_detail(inspectie),
                            ).props("dense flat color=primary").tooltip("Details")

                            count = len(storage.get(STORAGE_KEY, {}))
                            if count > 0:
                                ui.button(
                                    str(count),
                                    on_click=lambda: ui.navigate.to("/inspectie"),
                                ).props("dense flat color=accent").tooltip(
                                    f"{count} openstaande wijzigingen"
                                )

    card()


@router.page("/view/{id}")
def view_batch(id: int) -> None:
    """Mobile-optimized view of batch information."""
    try:
        lot = get_repository().get_by_id(id)
        inspectie = InspectieRepository().get_by_id(str(id)) if lot is not None else None

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
                        "Oppotdatum": format_date(lot.oppot_datum),
                        "Stuks": lot.aantal_pot,
                    }
                )

                render_klant_afleverdatum_card(lot, inspectie)

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
