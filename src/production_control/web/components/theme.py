"""Theme and layout components."""

from contextlib import contextmanager
from .menu import menu
from .message import message
from nicegui import ui
import os
from fastapi import Request
from nicegui import context


def get_current_user():
    """Get the current authenticated user information from Authelia headers.

    Returns:
        dict: User information with keys 'name', 'roles', 'email', and 'profile_page'
    """
    user_info = {"name": "Guest", "roles": [], "email": "", "profile_page": ""}

    try:
        request: Request = context.client.request
        user_name = request.headers.get("remote-user") or request.headers.get("remote-name")
        if user_name:
            user_info["name"] = user_name

        email = request.headers.get("remote-email")
        if email:
            user_info["email"] = email

        groups = request.headers.get("remote-groups")
        if groups:
            user_info["roles"] = [group.strip() for group in groups.split(",")]

        # Check for profile page URL from environment variable
        profile_url = os.getenv("PROFILE_PAGE_URL")
        if profile_url:
            user_info["profile_page"] = profile_url

    except Exception as e:
        print(f"Error getting user info: {e}")

    return user_info


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

        # Right section: User name and page title
        with ui.row().classes("items-center gap-4"):
            # User display
            user = get_current_user()
            user_name = user["name"]
            user_roles = user["roles"]
            profile_page = user["profile_page"]

            # Create tooltip text with groups/roles
            if user_roles:
                tooltip_text = f"Roles: {', '.join(user_roles)}"
            else:
                tooltip_text = "No roles assigned"

            # Display user name as link or label
            if profile_page:
                ui.link(user_name, profile_page).classes(
                    "text-lg text-white/90 no-underline"
                ).tooltip(tooltip_text)
            else:
                ui.label(user_name).classes("text-lg text-white/90").tooltip(tooltip_text)

            # Page title
            ui.label(navigation_title).classes("text-lg text-white/90")

    # Main content with error handling
    with ui.element("main").classes("w-full flex-grow"):
        with ui.column().classes("w-full items-center p-4"):
            try:
                yield
            except Exception as e:
                message(f"Error: {str(e)}")
                if "PYTEST_CURRENT_TEST" in os.environ:
                    raise  # Re-raise the exception if in a testing run
