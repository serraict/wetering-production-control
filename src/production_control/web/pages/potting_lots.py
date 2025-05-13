"""Potting lots page implementation."""

from typing import Dict, Any, List, Union
from datetime import date

from nicegui import APIRouter, ui

from ...potting_lots.repositories import PottingLotRepository
from ...potting_lots.models import PottingLot
from ...potting_lots.label_generation import LabelGenerator
from ..components import frame
from ..components.model_detail_page import display_model_detail_page, create_model_view_action
from ..components.model_list_page import display_model_list_page
from ..components.table_state import ClientStorageTableState


router = APIRouter(prefix="/potting-lots")
label_generator = LabelGenerator()
table_state_key = "potting_lots_table"


def generate_and_download_pdf(records: Union[PottingLot, List[PottingLot]], filename: str) -> None:
    """
    Generate a PDF for records and trigger download.

    Args:
        records: A single PottingLot record or a list of records
        filename: Name for the downloaded file
    """
    pdf_path = label_generator.generate_pdf(records)

    if not pdf_path:
        return

    # Download the PDF
    ui.download(pdf_path, filename=filename)

    # Clean up the temporary file after download
    label_generator.cleanup_pdf(pdf_path)


def create_label_action() -> Dict[str, Any]:

    def handle_label(e: Dict[str, Any]) -> None:
        id_value = e.args.get("key")

        # Get record from table state instead of database
        table_state = ClientStorageTableState.initialize(table_state_key)
        record = next(
            (PottingLot(**row) for row in table_state.rows if row["id"] == id_value), None
        )

        if record:
            # Create a descriptive filename
            filename = f"oppotpartij_{record.id}_{record.naam.replace(' ', '_')}.pdf"
            generate_and_download_pdf(record, filename)

    return {
        "icon": "print",
        "tooltip": "Druk 2 labels af (begin en eind)",
        "handler": handle_label,
    }


def handle_print_all() -> None:
    # Get the current table state
    table_state = ClientStorageTableState.initialize(table_state_key)

    # Create PottingLot items from table state rows
    records = [PottingLot(**visible_row) for visible_row in table_state.rows]

    if not records:
        return

    # Create a descriptive filename using today with format %gW%V-%u
    filename = f"oppotpartijen_{date.today():%gW%V-%u}.pdf"
    generate_and_download_pdf(records, filename)


@router.page("/")
def potting_lots_page() -> None:
    """Display the potting lots page."""
    repository = PottingLotRepository()

    row_actions = {
        "view": create_model_view_action(
            repository=repository,
        ),
        "label": create_label_action(),
    }

    with frame("Oppotlijst"):

        with ui.row().classes("w-full justify-end mb-4"):
            with ui.button("Labels Afdrukken", icon="print").classes("bg-primary") as button:
                ui.tooltip("Druk labels af voor alle zichtbare records (2 labels per partij: begin en eind)")
                button.on_click(handle_print_all)

        display_model_list_page(
            repository=repository,
            model_cls=PottingLot,
            table_state_key=table_state_key,
            title="Oppotlijst",
            row_actions=row_actions,
        )


@router.page("/{id}")
def potting_lot_detail(id: int) -> None:
    repository = PottingLotRepository()
    record = repository.get_by_id(id)

    with frame("Oppotlijst Details"):
        display_model_detail_page(
            model=record,
            title="Oppotlijst Details",
            back_link_text="← Terug naar Oppotlijst",
            back_link_url="/potting-lots",
        )


@router.page("/scan/{id}")
def potting_lot_scan(id: int) -> None:
    ui.navigate.to(router.url_path_for("potting_lot_detail", id=id))
