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
        id_value = e.args.get("key")
        record = repository.get_by_id(id_value)
        if record:
            label_generator = LabelGenerator()
            base_url = os.environ.get("QR_CODE_BASE_URL", "")
            if not base_url:
                base_url = next(iter(app.urls), "")

            pdf_path = label_generator.generate_pdf(record, base_url=base_url)

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


@router.page("/")
def bulb_picklist_page() -> None:
    repository = BulbPickListRepository()

    row_actions = {
        "view": create_model_view_action(
            repository=repository,
        ),
        "label": create_label_action(repository),
    }

    with frame("Bollen Picklist"):
        display_model_list_page(
            repository=repository,
            model_cls=BulbPickList,
            table_state_key="bulb_picklist_table",
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
