"""Message components for displaying errors and other notifications."""

from nicegui import ui


def message(text: str, type: str = "error") -> None:
    """Display a message using a notification.

    Args:
        text: The message text to display
        type: The message type ("error" by default, can be "positive", "negative", "warning", "info")
    """
    # Map error type to negative for consistency with Quasar's types
    notify_type = "negative" if type == "error" else type
    ui.notify(
        text,
        type=notify_type,
        position="top",
        close_button="Close",
        multi_line=True,
    )


def show_error(text: str) -> None:
    """Display an error message.

    Args:
        text: The error message to display
    """
    message(text, type="error")
