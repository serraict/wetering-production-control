"""Component for displaying model list pages."""

from typing import Dict, Any, Callable, Optional, Type
from nicegui import ui

from .styles import CARD_CLASSES, HEADER_CLASSES
from .data_table import server_side_paginated_table
from .table_utils import format_row
from .table_state import ClientStorageTableState


def display_model_list_page(
    repository: Any,
    model_cls: Type,
    table_state_key: str,
    title: str,  # to do: remove this parameter
    row_actions: Dict[str, Dict[str, Any]],
    card_width: str = "max-w-7xl",  # to do: remove this parameter
    filter_placeholder: str = "Zoek ...",  # to do: remove this parameter
    custom_filters: Optional[Callable[[ui.row], None]] = None,
    custom_load_data: Optional[Callable[[Any, Any], Callable]] = None,
) -> None:
    """Display a model list page with standard layout.

    Args:
        repository: The repository to use for fetching models
        model_cls: The model class
        table_state_key: The key to use for storing table state
        title: The page title
        row_actions: Dictionary of row actions
        card_width: The width of the card (default: "max-w-5xl")
        filter_placeholder: Placeholder text for the filter input
        custom_filters: Optional function to add custom filters to the filter row
    """
    # Set up table data access
    table_state = ClientStorageTableState.initialize(table_state_key)

    # Use custom load_data function if provided, otherwise use default - why doe we need this?
    if custom_load_data:
        load_data = custom_load_data(repository, table_state)
        # If a store_load_data function is provided, use it to store the load_data function
        if (
            hasattr(custom_load_data, "__globals__")
            and "store_load_data" in custom_load_data.__globals__
        ):
            store_load_data = custom_load_data.__globals__["store_load_data"]
            load_data = store_load_data(load_data)
    else:

        def load_data():
            pagination = table_state.pagination
            filter_text = table_state.filter
            items, total = repository.get_paginated(
                pagination=pagination,
                filter_text=filter_text,
            )
            table_state.update_rows([format_row(item) for item in items], total)
            server_side_paginated_table.refresh()

    # event handlers
    async def handle_filter(e: Any) -> None:
        """Handle changes to the search filter."""
        table_state.update_filter(e.value if e.value else "")
        load_data()

    def handle_table_request(event: Dict[str, Any]) -> None:
        """Handle table request events."""
        table_state.update_from_request(event)
        load_data()

    # render page
    with ui.card().classes(CARD_CLASSES.replace("max-w-3xl", card_width)):
        with ui.row().classes("w-full justify-between items-center mb-4"):
            ui.label("Overzicht").classes(HEADER_CLASSES)
            with ui.row().classes("gap-4"):
                # Add custom filters if provided
                if custom_filters:
                    custom_filters(ui.row().classes("gap-4"))

                # Search input
                with (
                    ui.input(
                        filter_placeholder,
                        on_change=lambda e: handle_filter(e),
                    )
                    .classes("w-64")
                    .props("debounce=500")
                    .mark("search") as search
                ):
                    with search.add_slot("append"):
                        ui.icon("search")

        server_side_paginated_table(
            cls=model_cls,
            state=table_state,
            on_request=handle_table_request,
            row_actions=row_actions,
        )

    # load initial data
    load_data()
