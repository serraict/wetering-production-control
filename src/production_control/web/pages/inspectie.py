"""Inspectie page implementation."""

from typing import Dict, Any

from nicegui import APIRouter, ui

from ...inspectie.repositories import InspectieRepository
from ...inspectie.models import InspectieRonde
from ..components import frame
from ..components.model_list_page import display_model_list_page


router = APIRouter(prefix="/inspectie")


def create_afwijking_actions() -> Dict[str, Any]:
    """Create row actions for +1/-1 buttons."""

    def handle_plus_one(e: Dict[str, Any]) -> None:
        """Handle +1 button click."""
        code = e.args.get("key")
        # TODO: Implement command to update afwijking_afleveren +1
        ui.notify(f"Afwijking +1 voor {code}", type="positive")

    def handle_minus_one(e: Dict[str, Any]) -> None:
        """Handle -1 button click."""
        code = e.args.get("key")
        # TODO: Implement command to update afwijking_afleveren -1
        ui.notify(f"Afwijking -1 voor {code}", type="positive")

    return {
        "plus_one": {
            "icon": "add",
            "tooltip": "Afwijking +1",
            "handler": handle_plus_one,
        },
        "minus_one": {
            "icon": "remove",
            "tooltip": "Afwijking -1",
            "handler": handle_minus_one,
        },
    }


@router.page("/")
def inspectie_page() -> None:
    """Render the inspectie ronde overview page."""
    repository = InspectieRepository()

    # Create actions for +1/-1 buttons
    row_actions = create_afwijking_actions()

    # Render page
    with frame("Inspectie Ronde"):
        with ui.row().classes("w-full justify-between items-center mb-4"):
            ui.label("Inspectie Ronde").classes("text-h4")
            ui.button(
                "Print", icon="print", on_click=lambda: ui.run_javascript("window.print()")
            ).props("outline")

        display_model_list_page(
            repository=repository,
            model_cls=InspectieRonde,
            table_state_key="inspectie_table",
            title="Inspectie Ronde",
            row_actions=row_actions,
        )
