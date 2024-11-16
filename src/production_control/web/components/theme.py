"""Theme and layout components."""

from contextlib import contextmanager
from .menu import menu
from .message import message
from nicegui import ui


@contextmanager
def frame(navigation_title: str):
    """Create a themed frame with header and navigation.

    Args:
        navigation_title: The title to display in the navigation bar
    """
    ui.colors(
        brand="#009279",
        primary="#009279",
        secondary="#b5d334",
        accent="#f39c21",
        positive="#b5d334",
        negative="#ad1b11",
        info="#c5b4ff",
        warning="#d38334",
    )

    with ui.header().classes(
        "w-full px-6 py-2 bg-primary flex justify-between items-center"
    ):
        # Left section: App logo and navigation
        with ui.row().classes("items-center gap-8"):
            # Logo that navigates home on click
            with (
                ui.element("a")
                .classes("flex items-center gap-1 no-underline cursor-pointer")
                .on("click", lambda: ui.navigate.to("/"))
            ):
                # Data pipeline icon
                ui.icon("account_tree", color="white").classes("text-xl")
                # Leaf icon overlapping slightly
                ui.icon("eco", color="white").classes("text-lg -ml-1")
            menu()

        # Right section: Page title
        ui.label(navigation_title).classes("text-lg text-white/90")

    # Main content with error handling
    with ui.element("main").classes("w-full flex-grow"):
        with ui.column().classes("w-full items-center p-4"):
            try:
                yield
            except Exception as e:
                message(f"Error: {str(e)}")
