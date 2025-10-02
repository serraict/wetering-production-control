"""Server-side paginating table component."""

from typing import Optional, Type, List, Any, Dict, Callable
from sqlmodel import SQLModel
from nicegui import ui

from .table_utils import get_table_columns
from .table_state import ClientStorageTableState
from ...data import Pagination


class ServerSidePaginatingTable(ui.table):
    """Table component with server-side pagination."""

    def __init__(
        self,
        model_class: Type[SQLModel],
        rows: List[Any],
        pagination: Pagination,
        row_key: str = "id",
        title: Optional[str] = None,
    ) -> None:
        """Initialize table with server-side pagination.

        Args:
            model_class: SQLModel class that defines the table structure
            rows: List of row data
            pagination: Pagination instance for state management
            row_key: Field to use as row key
            title: Optional table title
        """
        columns = get_table_columns(model_class)
        super().__init__(
            columns=columns,
            rows=rows,
            row_key=row_key,
            title=title,
            pagination=pagination.to_dict(),
        )
        self.classes("w-full")


@ui.refreshable
def server_side_paginated_table(
    cls: Type[SQLModel],
    state: ClientStorageTableState,
    on_request: Callable,
    title: str = "Items",
    row_key: str = "id",
    row_actions: Dict[str, Dict[str, Any]] = {},
    enable_fullscreen: bool = False,
) -> ui.table:
    """Create a refreshable table component.

    Args:
        cls: SQLModel class that defines the table structure
        state: ClientStorageTableState instance for state management
        on_request: Callback for handling table requests (pagination/sorting)
        title: Optional table title
        row_actions: Optional dict of row actions, each with 'icon' and 'handler'
        enable_fullscreen: Whether to enable fullscreen toggle button

    Returns:
        A refreshable table component
    """
    table = ServerSidePaginatingTable(
        model_class=cls,
        rows=state.rows,
        row_key=row_key,
        title=title,
        pagination=state.pagination,
    )

    btns = [
        f"""
            <q-btn @click="$parent.$emit('{action_key}', props)" icon="{action['icon']}" flat dense color='primary'/>
            """
        for action_key, action in row_actions.items()
    ]

    if btns:
        table.add_slot(
            "body-cell-actions",
            f"""
            <q-td :props="props">
                {''.join(btns)}
            </q-td>
        """,
        )

    for action_key, action in row_actions.items():
        table.on(action_key, action["handler"])

    # Add fullscreen functionality if enabled
    if enable_fullscreen:
        with table.add_slot("top-left"):

            def toggle_fullscreen():
                table.toggle_fullscreen()
                fullscreen_button.props(
                    "icon=fullscreen_exit" if table.is_fullscreen else "icon=fullscreen"
                )

            fullscreen_button = (
                ui.button("Volledig scherm", icon="fullscreen", on_click=toggle_fullscreen)
                .props("flat")
                .tooltip("Schakelen naar volledig scherm")
            )

    table.on("request", on_request)
    return table
