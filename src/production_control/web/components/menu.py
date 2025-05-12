"""Navigation menu component."""

from nicegui import ui
from .styles import MENU_LINK_CLASSES


def menu() -> None:
    """Render the navigation menu."""
    with ui.row().classes("gap-6"):
        ui.link("Producten", "/products").classes(MENU_LINK_CLASSES)
        ui.link("Wijderzetten", "/spacing").classes(MENU_LINK_CLASSES)
        ui.link("Bollen Picklist", "/bulb-picking").classes(MENU_LINK_CLASSES)
        ui.link("Oppotlijst", "/potting-lots").classes(MENU_LINK_CLASSES)
        ui.link("About", "/about").classes(MENU_LINK_CLASSES)
