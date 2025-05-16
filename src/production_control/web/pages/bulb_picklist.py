"""Bulb picklist page implementation."""

from typing import Dict, Any
from datetime import date

from nicegui import APIRouter, ui, run

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


def generate_labels(records, filename=None) -> str:
    label_generator = LabelGenerator()
    return label_generator.generate_pdf(records)


def create_label_action() -> Dict[str, Any]:

    async def handle_label(e: Dict[str, Any]) -> None:
        id_value = e.args.get("key")
        table_state = ClientStorageTableState.initialize(table_state_key)
        record = next(
            (BulbPickList(**row) for row in table_state.rows if row["id"] == id_value), None
        )

        if record:
            # Create a descriptive filename, this is used for the downloaded file for the user
            filename = f"label_{record.id}_{record.ras.replace(' ', '_')}.pdf"
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
        "handler": handle_label,
    }


async def handle_print_all() -> None:
    table_state = ClientStorageTableState.initialize(table_state_key)
    records = [BulbPickList(**visible_row) for visible_row in table_state.rows]

    if not records:
        return

    ui.notify("Generating labels...")

    try:
        # Generate labels in background process
        pdf_path = await run.cpu_bound(generate_labels, records)

        # Download and cleanup
        filename = f"labels_{date.today():%gW%V-%u}.pdf"
        ui.download(pdf_path, filename=filename)
        label_generator.cleanup_pdf(pdf_path)

    except Exception as e:
        msg = f"Error generating labels: {str(e)}"
        print(msg)
        ui.notify(msg)


@router.page("/")
async def bulb_picklist_page() -> None:
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
            print_all_caption = "Labels Afdrukken"
            print_all_icon = "print"
            with ui.button(print_all_caption, icon=print_all_icon).classes(
                "bg-primary"
            ) as print_all_button:
                ui.tooltip("Druk labels af voor alle zichtbare records")

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
