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
                ui.label("Welcome to Production Control").classes(
                    HEADER_CLASSES
                )

            # Main content section
            with ui.column().classes("w-full items-center gap-4"):
                ui.label("A Serra Vine application.").classes(SUBHEADER_CLASSES)

                # Navigation cards
                with ui.row().classes("w-full gap-4 justify-center mt-4"):
                    with ui.card().classes(NAV_CARD_CLASSES):
                        ui.label("Products").classes(HEADER_CLASSES + " mb-2")
                        ui.label("View and manage your products").classes(
                            SUBHEADER_CLASSES + " mb-4"
                        )
                        ui.link("View Products", "/products").classes(LINK_CLASSES)

                    with ui.card().classes(NAV_CARD_CLASSES):
                        ui.label("About").classes(HEADER_CLASSES + " mb-2")
                        ui.label(
                            "Learn more about Production Control"
                        ).classes(SUBHEADER_CLASSES + " mb-4")
                        ui.link("About", "/about").classes(LINK_CLASSES)


@root_router.page("/about")
def about_page() -> None:
    """Render the about page with application information."""
    info = get_application_info()

    with frame("About"):
        display_model_card(info, description_field="description")
