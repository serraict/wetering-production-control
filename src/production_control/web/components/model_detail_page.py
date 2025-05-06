"""Component for displaying model detail pages."""

from typing import Optional, Any, Dict, Callable
from pydantic import BaseModel
from nicegui import ui

from .model_card import display_model_card
from .styles import LINK_CLASSES
from .message import show_error


def display_model_detail_page(
    model: Optional[BaseModel],
    title: str,
    back_link_text: str,
    back_link_url: str,
    model_title_field: Optional[str] = None,
    custom_display_function: Optional[Callable[[BaseModel], None]] = None,
) -> None:
    """Display a model detail page with standard layout.

    Args:
        model: The model instance to display, or None if not found
        title: The page title
        back_link_text: Text for the back link
        back_link_url: URL for the back link
        model_title_field: Optional field to use as the model title
        custom_display_function: Optional function to display the model instead of using display_model_card
    """
    with ui.row().classes("w-full justify-between items-center mb-6"):
        ui.link(back_link_text, back_link_url).classes(LINK_CLASSES)

    if model:
        if custom_display_function:
            custom_display_function(model)
        else:
            model_title = getattr(model, model_title_field) if model_title_field else str(model)
            display_model_card(model, title=model_title)
    else:
        # Display error message as a visible element on the page
        ui.label("Record niet gevonden").classes("text-negative text-h6")
        ui.link(back_link_text, back_link_url).classes(LINK_CLASSES + " mt-4")
        # Also show notification
        show_error("Record niet gevonden")


def create_model_view_action(
    repository: Any,
    id_field: str = "id",
    dialog: bool = True,
    detail_url: Optional[str] = None,
    custom_display_function: Optional[Callable[[BaseModel], None]] = None,
) -> Dict[str, Any]:
    """Create a view action for a model.

    Args:
        repository: The repository to use for fetching the model
        id_field: The field name to use as the ID (default: "id")
        dialog: Whether to show the model in a dialog (True) or navigate to a detail page (False)
        detail_url: The URL pattern for the detail page, with {id} placeholder
        custom_display_function: Optional function to display the model instead of using display_model_card

    Returns:
        A dictionary with the view action configuration
    """
    if dialog:

        def handle_view(e: Dict[str, Any]) -> None:
            """Handle view button click."""
            id_value = e.args.get("key")
            record = repository.get_by_id(id_value)
            if record:
                with ui.dialog() as dialog, ui.card():
                    if custom_display_function:
                        custom_display_function(record)
                    else:
                        display_model_card(record)
                    ui.button("Sluiten", on_click=dialog.close)
                    dialog.open()
            else:
                show_error("Record niet gevonden")

        return {
            "icon": "visibility",
            "handler": handle_view,
        }
    else:
        return {
            "icon": "visibility",
            "handler": lambda e: ui.navigate.to(detail_url.format(id=e.args.get("key"))),
        }
