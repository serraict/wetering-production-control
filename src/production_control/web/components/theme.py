"""Theme and layout components."""

from contextlib import contextmanager
from .menu import menu
from .message import message
from nicegui import ui
from ..auth import get_current_user
import os


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

    with ui.header().classes("w-full px-6 py-2 bg-primary flex justify-between items-center"):
        # Left section: Navigation menu
        with ui.row().classes("items-center gap-8"):
            menu()

        # Center section: Page title
        ui.label(navigation_title).classes("text-lg text-white/90")

        # Right section: Scan button and User menu
        with ui.row().classes("items-center gap-4"):
            # Scan button
            ui.button(icon="qr_code_scanner", on_click=lambda: ui.navigate.to("/scan")).props(
                "flat"
            ).classes("text-white").tooltip("Scan Batch")

            # User menu with icon
            user = get_current_user()
            user_name = user["name"]
            user_roles = user["roles"]
            profile_page = user["profile_page"]

            # User icon with dropdown menu
            with ui.button(icon="account_circle").props("flat").classes("text-white"):
                with ui.menu():
                    # User name at top (as link if profile page exists)
                    if profile_page:
                        ui.menu_item(user_name, lambda: ui.navigate.to(profile_page))
                    else:
                        ui.menu_item(user_name, auto_close=False)

                    # Separator
                    ui.separator()

                    # Display roles
                    if user_roles:
                        for role in user_roles:
                            ui.menu_item(f"Role: {role}", auto_close=False)
                    else:
                        ui.menu_item("No roles assigned", auto_close=False)

    # Main content with error handling
    with ui.element("main").classes("w-full flex-grow"):
        with ui.column().classes("w-full items-center p-4"):
            try:
                yield
            except Exception as e:
                message(f"Error: {str(e)}")
                if "PYTEST_CURRENT_TEST" in os.environ:
                    raise  # Re-raise the exception if in a testing run
