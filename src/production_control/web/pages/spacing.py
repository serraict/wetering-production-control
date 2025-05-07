"""Spacing page implementation."""

from typing import Dict, Any, Callable

from nicegui import APIRouter, ui
from pydantic import ValidationError

from ...spacing.repositories import SpacingRepository
from ...spacing.models import WijderzetRegistratie
from ...spacing.commands import CorrectSpacingRecord
from ...spacing.optech import OpTechClient, OpTechError
from ..components import frame
from ..components.model_card import display_model_card
from ..components.message import show_error
from ..components.command_form import create_command_form
from ..components.model_detail_page import display_model_detail_page, create_model_view_action
from ..components.model_list_page import display_model_list_page


router = APIRouter(prefix="/spacing")


def create_correction_form(record: WijderzetRegistratie, on_close: Callable[[], None]) -> None:
    title = f"{record.partij_code} - {record.product_naam}"

    # Create command and form
    client = OpTechClient()
    command = CorrectSpacingRecord.from_record(record)

    def handle_save(updated: CorrectSpacingRecord) -> None:
        """Handle save button click."""
        try:
            client.send_correction(updated)
            ui.notify(f"Wijzigingen opgeslagen voor {record.partij_code}")
            on_close()
        except ValidationError as e:
            # Show first error message
            error = e.errors()[0]
            ui.notify(error["msg"], type="negative", timeout=5000)
        except OpTechError as e:
            ui.notify(str(e), type="negative", timeout=5000)

    ui.label(title)

    if record.wijderzet_registratie_fout:
        with ui.card().classes("mb-4 bg-warning bg-opacity-10"):
            ui.label("Fout").classes("text-lg font-bold")
            ui.label(record.wijderzet_registratie_fout)

    create_command_form(command, handle_save, on_close)


def display_spacing_record(record: WijderzetRegistratie) -> None:
    if record.wijderzet_registratie_fout:
        with ui.card().classes("mt-4 bg-warning bg-opacity-10"):
            ui.label("Fout").classes("text-lg font-bold")
            ui.label(record.wijderzet_registratie_fout)

    display_model_card(record, title=str(record))


def create_edit_action(repository: SpacingRepository) -> Dict[str, Any]:

    def handle_edit(e: Dict[str, Any]) -> None:
        """Handle edit button click."""
        partij_code = e.args.get("key")
        record = repository.get_by_id(partij_code)
        if record:
            with ui.dialog() as dialog, ui.card():
                create_correction_form(record, dialog.close)
                dialog.open()
        else:
            show_error("Record niet gevonden")

    return {
        "icon": "edit",
        "handler": handle_edit,
    }


@router.page("/")
def spacing_page() -> None:

    repository = SpacingRepository()

    # Create actions
    row_actions = {
        "view": create_model_view_action(
            repository=repository,
            dialog=True,
            custom_display_function=display_spacing_record,
        ),
        "edit": create_edit_action(repository),
    }

    # Render page
    with frame("Wijderzetten"):
        display_model_list_page(
            repository=repository,
            model_cls=WijderzetRegistratie,
            table_state_key="spacing_table",
            title="Wijderzetten",
            row_actions=row_actions,
        )


@router.page("/{partij_code}")
def spacing_detail(partij_code: str) -> None:
    """Render the spacing record detail page."""
    repository = SpacingRepository()
    record = repository.get_by_id(partij_code)

    with frame("Wijderzet Details"):
        display_model_detail_page(
            model=record,
            title="Wijderzet Details",
            back_link_text="← Terug naar Wijderzetten",
            back_link_url="/spacing",
            custom_display_function=display_spacing_record,
        )


@router.page("/correct/{partij_code}")
def spacing_correct(partij_code: str) -> None:
    """Render the spacing record correction page."""
    repository = SpacingRepository()
    record = repository.get_by_id(partij_code)

    with frame("Wijderzet Correctie"):
        if record:
            with ui.row().classes("w-full justify-between items-center mb-6"):
                ui.link("← Terug naar Wijderzetten", "/spacing").classes(
                    "text-blue-500 hover:underline"
                )

            with ui.card().classes("p-4 max-w-3xl mx-auto"):
                create_correction_form(record, lambda: ui.navigate.to("/spacing"))
        else:
            ui.label("Record niet gevonden").classes("text-negative text-h6")
            ui.link("← Terug naar Wijderzetten", "/spacing").classes(
                "text-blue-500 hover:underline mt-4"
            )
