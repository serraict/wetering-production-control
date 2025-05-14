"""Bulb picklist page implementation."""

from typing import Dict, Any, List, Union
from datetime import date

from nicegui import APIRouter, ui

from ...bulb_picklist.repositories import BulbPickListRepository
from ...bulb_picklist.models import BulbPickList
from ...bulb_picklist.label_generation import LabelGenerator
from ..components import frame
from ..components.model_detail_page import display_model_detail_page, create_model_view_action
from ..components.model_list_page import display_model_list_page
from ..components.table_state import ClientStorageTableState


router = APIRouter(prefix="/bulb-picking")
label_generator = LabelGenerator()
table_state_key = "bulb_picklist_table"


def generate_and_download_pdf(
    records: Union[BulbPickList, List[BulbPickList]], filename: str
) -> None:
    pdf_path = label_generator.generate_pdf(records)

    if not pdf_path:
        return

    ui.download(pdf_path, filename=filename)

    label_generator.cleanup_pdf(pdf_path)


def create_label_action() -> Dict[str, Any]:

    def handle_label(e: Dict[str, Any]) -> None:
        id_value = e.args.get("key")
        table_state = ClientStorageTableState.initialize(table_state_key)
        record = next(
            (BulbPickList(**row) for row in table_state.rows if row["id"] == id_value), None
        )

        if record:
            filename = f"label_{record.id}_{record.ras.replace(' ', '_')}.pdf"
            generate_and_download_pdf(record, filename)

    return {
        "icon": "print",
        "handler": handle_label,
    }


def handle_print_all() -> None:
    table_state = ClientStorageTableState.initialize(table_state_key)
    records = [BulbPickList(**visible_row) for visible_row in table_state.rows]

    if not records:
        return

    filename = f"labels_{date.today():%gW%V-%u}.pdf"
    generate_and_download_pdf(records, filename)


@router.page("/")
def bulb_picklist_page() -> None:
    """Display the bulb picklist page."""
    repository = BulbPickListRepository()

    row_actions = {
        "view": create_model_view_action(
            repository=repository,
        ),
        "label": create_label_action(),
    }

    with frame("Bollen Picklist"):

        with ui.row().classes("w-full justify-end mb-4"):
            with ui.button("Labels Afdrukken", icon="print").classes("bg-primary") as button:
                ui.tooltip("Druk labels af voor alle zichtbare records")
                button.on_click(handle_print_all)

        display_model_list_page(
            repository=repository,
            model_cls=BulbPickList,
            table_state_key=table_state_key,
            title="Bollen Picklist",
            row_actions=row_actions,
        )


@router.page("/{id}")
def bulb_picklist_detail(id: int) -> None:
    repository = BulbPickListRepository()
    record = repository.get_by_id(id)

    with frame("Bollen Picklist Details"):
        display_model_detail_page(
            model=record,
            title="Bollen Picklist Details",
            back_link_text="← Terug naar Bollen Picklist",
            back_link_url="/bulb-picking",
        )


@router.page("/scan/{id}")
def bulb_picklist_scan(id: int) -> None:
    ui.navigate.to(router.url_path_for("bulb_picklist_detail", id=id))
