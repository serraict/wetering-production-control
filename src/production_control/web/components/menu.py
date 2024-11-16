"""Navigation menu component."""

from nicegui import ui
from .styles import MENU_LINK_CLASSES


def menu() -> None:
    """Render the navigation menu."""
    with ui.row().classes("gap-6"):
        ui.link("Products", "/products").classes(MENU_LINK_CLASSES)
        ui.link("About", "/about").classes(MENU_LINK_CLASSES)
