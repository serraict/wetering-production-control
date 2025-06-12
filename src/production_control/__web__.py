"""Web interface for Production Control."""

import os
from nicegui import app, ui

from .web.startup import startup


def init() -> None:
    """Initialize the web application."""
    # Clear any default page layout
    app.on_startup(startup)


if __name__ in {"__main__", "__mp_main__"}:
    init()
    port = int(os.getenv("NICEGUI_PORT", "8080"))
    ui.run(title="Production Control", port=port)
