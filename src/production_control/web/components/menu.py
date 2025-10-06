"""Navigation menu component."""

from nicegui import ui


def menu() -> None:
    """Render the navigation menu."""
    with ui.element():
        with ui.button(icon="menu").props("flat").classes("text-white"):
            with ui.menu():
                ui.menu_item("Home", lambda: ui.navigate.to("/"))
                ui.menu_item("Bollen Picklist", lambda: ui.navigate.to("/bulb-picking"))
                ui.menu_item("Oppotlijst", lambda: ui.navigate.to("/potting-lots"))
                ui.menu_item("Wijderzetten", lambda: ui.navigate.to("/spacing"))
                ui.menu_item("Inspectie Ronde", lambda: ui.navigate.to("/inspectie"))
                with ui.menu_item("Info", auto_close=False):
                    with ui.item_section().props("side"):
                        ui.icon("keyboard_arrow_right")
                    with ui.menu().props('anchor="top end" self="top start" auto-close'):
                        ui.menu_item("Producten", lambda: ui.navigate.to("/products"))
                        ui.menu_item("About", lambda: ui.navigate.to("/about"))
