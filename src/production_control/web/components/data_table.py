"""Data table component."""

from typing import Optional, Type
from sqlmodel import SQLModel
from nicegui import ui

from .table_utils import get_table_columns


class DataTable(ui.table):
    """Table component with model-driven columns."""

    def __init__(
        self,
        model_class: Type[SQLModel],
        rows: list = None,
        row_key: str = "id",
        title: Optional[str] = None,
    ) -> None:
        """Initialize data table.

        Args:
            model_class: SQLModel class that defines the table structure
            rows: Optional list of rows
            row_key: Field to use as row key
            title: Optional table title
        """
        columns = get_table_columns(model_class)
        super().__init__(
            columns=columns,
            rows=rows or [],
            row_key=row_key,
            title=title,
        )
        self.classes("w-full")
