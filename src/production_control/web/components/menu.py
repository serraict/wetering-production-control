"""Navigation menu component."""

from nicegui import ui


def menu() -> None:
    """Render the navigation menu."""
    with ui.element():
        with ui.button(icon="menu").props("flat").classes("text-white"):
            with ui.menu():
                ui.menu_item("Producten", lambda: ui.navigate.to("/products"))
                ui.menu_item("Wijderzetten", lambda: ui.navigate.to("/spacing"))
                ui.menu_item("Inspectie Ronde", lambda: ui.navigate.to("/inspectie"))
                ui.menu_item("Bollen Picklist", lambda: ui.navigate.to("/bulb-picking"))
                ui.menu_item("Oppotlijst", lambda: ui.navigate.to("/potting-lots"))
                ui.menu_item("About", lambda: ui.navigate.to("/about"))
