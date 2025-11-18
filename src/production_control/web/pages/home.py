"""Home and about pages implementation."""

from nicegui import APIRouter, ui

from ...app_info import get_application_info
from ..components import frame
from ..components.model_card import display_model_card
from ..components.styles import (
    CARD_CLASSES,
    HEADER_CLASSES,
    SUBHEADER_CLASSES,
    LINK_CLASSES,
    NAV_CARD_CLASSES,
)


# Root router without parameters
root_router = APIRouter()


@root_router.page("/")
def index_page() -> None:
    """Render the homepage."""
    with frame("Homepage"):
        with ui.card().classes(CARD_CLASSES):
            # Header section
            with ui.row().classes("w-full justify-center mb-4"):
                ui.label("Welcome to Production Control").classes(HEADER_CLASSES)

            # Main content section
            with ui.column().classes("w-full items-center gap-4"):
                ui.label("A Serra Vine application.").classes(SUBHEADER_CLASSES)

                # Navigation cards
                with ui.row().classes("w-full gap-4 justify-center mt-4 flex-wrap"):

                    with ui.card().classes(NAV_CARD_CLASSES):
                        ui.label("Bollen Picklist").classes(HEADER_CLASSES + " mb-2")
                        ui.label(
                            "Beheer bollen picklijsten voor het verzamelen van bollen"
                        ).classes(SUBHEADER_CLASSES + " mb-4")
                        ui.link("Ga naar Bollen Picklist", "/bulb-picking").classes(LINK_CLASSES)

                    with ui.card().classes(NAV_CARD_CLASSES):
                        ui.label("Oppotlijst").classes(HEADER_CLASSES + " mb-2")
                        ui.label("Beheer oppotlijsten en activeer partijen voor productie").classes(
                            SUBHEADER_CLASSES + " mb-4"
                        )
                        ui.link("Ga naar Oppotlijst", "/potting-lots").classes(LINK_CLASSES)

                    with ui.card().classes(NAV_CARD_CLASSES):
                        ui.label("Wijderzetten").classes(HEADER_CLASSES + " mb-2")
                        ui.label("Registreer en corrigeer wijderzet handelingen").classes(
                            SUBHEADER_CLASSES + " mb-4"
                        )
                        ui.link("Ga naar Wijderzetten", "/spacing").classes(LINK_CLASSES)

                    with ui.card().classes(NAV_CARD_CLASSES):
                        ui.label("Inspectieronde").classes(HEADER_CLASSES + " mb-2")
                        ui.label("Voer inspectierondes uit en registreer afwijkingen").classes(
                            SUBHEADER_CLASSES + " mb-4"
                        )
                        ui.link("Ga naar Inspectieronde", "/inspectie").classes(LINK_CLASSES)

                    with ui.card().classes(NAV_CARD_CLASSES):
                        ui.label("Scan Batch").classes(HEADER_CLASSES + " mb-2")
                        ui.label("Scan batch labels om batch informatie te bekijken").classes(
                            SUBHEADER_CLASSES + " mb-4"
                        )
                        ui.link("Ga naar Scanner", "/scan").classes(LINK_CLASSES)


@root_router.page("/about")
def about_page() -> None:
    """Render the about page with application information."""
    info = get_application_info()

    with frame("About"):
        display_model_card(info, description_field="description")
