"""Web application startup configuration."""

from nicegui import app, ui

from .pages import home, products


def startup() -> None:
    """Initialize the web application."""

    # Define root page which for some reason cannot be done in the router.
    @ui.page("/")
    def root():
        home.index_page()

    # Include routers
    app.include_router(home.root_router)
    app.include_router(products.router)
