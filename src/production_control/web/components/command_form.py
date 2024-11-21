"""Generic form component for command models."""

from datetime import date
from decimal import Decimal
from typing import Any, Callable, TypeVar

from nicegui import ui
from pydantic import BaseModel

from .table_utils import format_date

T = TypeVar("T", bound=BaseModel)


def format_field_value(value: Any) -> str:
    """Format a field value for display."""
    if value is None:
        return ""
    if isinstance(value, date):
        return format_date(value)
    if isinstance(value, Decimal):
        return f"{value:.1f}"
    return str(value)


def format_field_label(field_name: str, description: str) -> str:
    """Format a field label for display."""
    # Remove any "Aantal" prefix since it's redundant in labels
    if description.startswith("Aantal "):
        description = description[7:]
    # Remove any "Datum van" prefix since we add "Datum: " later
    if description.startswith("Datum van "):
        description = description[9:]
    # Remove any "Naam van " prefix
    if description.startswith("Naam van "):
        description = description[9:]
    # Remove any "Code van " prefix
    if description.startswith("Code van "):
        description = description[9:]
    return description


def create_command_form(
    command: T,
    on_save: Callable[[T], None],
    on_cancel: Callable[[], None],
) -> None:
    """Create a form for editing a command.

    Args:
        command: The command to edit
        on_save: Callback when save is clicked, receives updated command
        on_cancel: Callback when cancel is clicked
    """
    # Read-only fields
    with ui.column().classes("gap-2 mb-4"):
        for field_name in command.get_readonly_fields():
            field = command.model_fields[field_name]
            value = getattr(command, field_name)
            if value is not None:
                label = format_field_label(field_name, field.description)
                formatted_value = format_field_value(value)
                ui.label(f"{label}: {formatted_value}")

    # Editable fields
    editors: dict[str, Any] = {}
    with ui.column().classes("w-full gap-4"):
        for field_name in command.get_editable_fields():
            field = command.model_fields[field_name]
            value = getattr(command, field_name)
            with ui.row().classes("items-center gap-4"):
                editor = (
                    ui.number(
                        label=format_field_label(field_name, field.description),
                        value=value,
                        min=0,
                    )
                    .classes("w-32")
                    .mark(field_name)
                )
                editors[field_name] = editor
                if hasattr(command, f"datum_{field_name}_real"):
                    date_value = getattr(command, f"datum_{field_name}_real")
                    if date_value:
                        ui.label(f"Datum: {format_date(date_value)}")

    # Buttons
    with ui.row().classes("w-full justify-end gap-4 mt-4"):
        ui.button(
            "Annuleren",
            on_click=on_cancel,
        ).classes("bg-gray-500")

        def handle_save() -> None:
            """Handle save button click."""
            # Update command with edited values
            updates = {
                name: editor.value
                for name, editor in editors.items()
            }
            updated_command = command.model_copy(update=updates)
            on_save(updated_command)

        ui.button(
            "Opslaan",
            on_click=handle_save,
        ).classes("bg-primary")
