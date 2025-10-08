"""Web application startup configuration."""

import logging
from nicegui import app, ui

from .pages import home, products, spacing, bulb_picklist, potting_lots, inspectie
from ..firebird.api import router as firebird_router


def startup() -> None:
    """Configure and start the web application."""

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Define root page which for some reason cannot be done in the router.
    @ui.page("/")
    def root():
        home.index_page()

    # Include routers
    app.include_router(home.root_router)
    app.include_router(products.router)
    app.include_router(spacing.router)
    app.include_router(bulb_picklist.router)
    app.include_router(potting_lots.router)
    app.include_router(inspectie.router)
    app.include_router(firebird_router)
