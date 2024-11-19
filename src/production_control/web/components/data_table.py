"""Server-side paginating table component."""

from typing import Optional, Type, List, Any
from sqlmodel import SQLModel
from nicegui import ui

from .table_utils import get_table_columns
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
