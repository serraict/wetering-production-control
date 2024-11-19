"""Server-side paginating table component."""

from typing import Optional, Type, Dict, Any
from sqlmodel import SQLModel
from nicegui import ui

from .table_utils import get_table_columns


class ServerSidePaginatingTable(ui.table):
    """Table component with server-side pagination."""

    def __init__(
        self,
        model_class: Type[SQLModel],
        rows: list = None,
        row_key: str = "id",
        title: Optional[str] = None,
        pagination: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize table with server-side pagination.

        Args:
            model_class: SQLModel class that defines the table structure
            rows: Optional list of rows
            row_key: Field to use as row key
            title: Optional table title
            pagination: Optional pagination state dictionary
        """
        columns = get_table_columns(model_class)
        super().__init__(
            columns=columns,
            rows=rows or [],
            row_key=row_key,
            title=title,
            pagination=pagination,
        )
        self.classes("w-full")
