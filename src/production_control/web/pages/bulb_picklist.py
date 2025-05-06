"""Bulb picklist page implementation."""

import os
from typing import Dict, Any

from nicegui import APIRouter, ui, app

from ...bulb_picklist.repositories import BulbPickListRepository
from ...bulb_picklist.models import BulbPickList
from ...bulb_picklist.label_generation import LabelGenerator
from ..components import frame
from ..components.model_detail_page import display_model_detail_page, create_model_view_action
from ..components.model_list_page import display_model_list_page


router = APIRouter(prefix="/bulb-picking")


def create_label_action(repository: BulbPickListRepository) -> Dict[str, Any]:

    def handle_label(e: Dict[str, Any]) -> None:
        """Handle label button click."""
        id_value = e.args.get("key")
        record = repository.get_by_id(id_value)
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
            def cleanup():
                if os.path.exists(pdf_path):
                    os.remove(pdf_path)

            ui.timer(5, cleanup, once=True)

    return {
        "icon": "print",
        "handler": handle_label,
    }


def display_bulb_picklist_record(record: BulbPickList) -> None:

    ui.label(f"{record.ras} ({record.bollen_code})").classes("text-h6 font-bold mb-4")
    ui.label(f"Locatie: {record.locatie}")
    ui.label(f"Aantal bakken: {record.aantal_bakken}")
    ui.label(f"Aantal bollen: {record.aantal_bollen}")
    ui.label(f"Oppot datum: {record.oppot_datum}")


@router.page("/")
def bulb_picklist_page() -> None:
    repository = BulbPickListRepository()

    # Create actions
    row_actions = {
        "view": create_model_view_action(
            repository=repository,
            dialog=True,
            custom_display_function=display_bulb_picklist_record,
        ),
        "label": create_label_action(repository),
    }

    # Render page
    with frame("Bollen Picklist"):
        display_model_list_page(
            repository=repository,
            model_cls=BulbPickList,
            table_state_key="bulb_picklist_table",
            title="Bollen Picklist",
            row_actions=row_actions,
            card_width="max-w-7xl",
            filter_placeholder="Zoek ...",
        )


@router.page("/{id}")
def bulb_picklist_detail(id: int) -> None:
    """Render the bulb picklist record detail page."""
    repository = BulbPickListRepository()
    record = repository.get_by_id(id)

    with frame("Bollen Picklist Details"):
        display_model_detail_page(
            model=record,
            title="Bollen Picklist Details",
            back_link_text="← Terug naar Bollen Picklist",
            back_link_url="/bulb-picking",
            custom_display_function=display_bulb_picklist_record,
        )


@router.page("/scan/{id}")
def bulb_picklist_scan(id: int) -> None:
    """Render the landing page for QR code scans."""
    repository = BulbPickListRepository()
    record = repository.get_by_id(id)

    with frame("Bollen Picklist Scan"):
        display_model_detail_page(
            model=record,
            title="Bollen Picklist Scan",
            back_link_text="← Terug naar Bollen Picklist",
            back_link_url="/bulb-picking",
            custom_display_function=display_bulb_picklist_record,
        )
