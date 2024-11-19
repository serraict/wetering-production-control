"""Utilities for working with tables."""

from typing import Dict, List, Any, Type
from sqlmodel import SQLModel
from pydantic_core._pydantic_core import PydanticUndefinedType


def get_table_columns(model_class: Type[SQLModel]) -> List[Dict[str, Any]]:
    """Generate table columns configuration from a SQLModel class.

    Uses model field metadata to configure columns:
    - title: Used as column label
    - sa_column_kwargs.info.ui_hidden: Skip field if True
    - sa_column_kwargs.info.ui_sortable: Make column sortable if True
    - sa_column_kwargs.info.ui_order: Order columns by this value

    Args:
        model_class: The SQLModel class to generate columns for

    Returns:
        List of column configurations for use with ui.table
    """
    columns = []

    # Get all model fields
    for field_name, field in model_class.model_fields.items():
        # Get UI metadata from SQLAlchemy column info
        sa_kwargs = getattr(field, "sa_column_kwargs", None)
        if isinstance(sa_kwargs, (PydanticUndefinedType, type(None))):
            sa_kwargs = {}
        field_info = sa_kwargs.get("info", {})

        # Skip hidden fields
        if field_info.get("ui_hidden"):
            continue

        # Create column config
        column = {
            "name": field_name,
            "label": field.title or field_name,
            "field": field_name,
        }

        # Add sortable if specified
        if field_info.get("ui_sortable"):
            column["sortable"] = True

        columns.append(column)

    # Sort columns by ui_order if specified
    def get_order(col_name: str) -> int:
        field = model_class.model_fields[col_name]
        sa_kwargs = getattr(field, "sa_column_kwargs", None)
        if isinstance(sa_kwargs, (PydanticUndefinedType, type(None))):
            return 999
        return sa_kwargs.get("info", {}).get("ui_order", 999)

    columns.sort(key=lambda col: get_order(col["name"]))

    # Add actions column at the end
    columns.append({"name": "actions", "label": "Acties", "field": "actions"})

    return columns


def format_row(model: SQLModel) -> Dict[str, Any]:
    """Format a model instance as a table row.

    Uses the same field metadata as get_table_columns to determine which fields to include.

    Args:
        model: The model instance to format

    Returns:
        Dictionary with field values for use in ui.table rows
    """
    row = {"id": model.id}  # Always include id for row key

    for field_name, field in model.__class__.model_fields.items():
        # Get UI metadata from SQLAlchemy column info
        sa_kwargs = getattr(field, "sa_column_kwargs", None)
        if isinstance(sa_kwargs, (PydanticUndefinedType, type(None))):
            sa_kwargs = {}
        field_info = sa_kwargs.get("info", {})

        # Skip hidden fields
        if field_info.get("ui_hidden"):
            continue

        # Add field value to row
        row[field_name] = getattr(model, field_name)

    return row
