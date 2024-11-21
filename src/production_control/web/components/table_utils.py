"""Utilities for working with tables."""

from datetime import date
from typing import Dict, List, Any, Type, get_args, get_origin
from sqlmodel import SQLModel
from pydantic_core._pydantic_core import PydanticUndefinedType


DATE_FORMAT = "%gw%V-%u"


def format_date(value: date, format_str: str = "YY[w]ww-E") -> str:
    """Format a date value using Quasar date format strings.

    Args:
        value: The date to format
        format_str: The format string to use (default: YY[w]ww-E)

    Returns:
        The formatted date string
    """
    if not value:
        return ""

    return value.strftime(DATE_FORMAT)  # ISO week number


def is_date_field(field_type: Any) -> bool:
    """Check if a field type is a date or Optional[date]."""
    if field_type == date:
        return True

    # Handle Optional[date]
    origin = get_origin(field_type)
    if origin is not None and origin.__name__ == "Union":
        args = get_args(field_type)
        return date in args

    return False


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

        # Add formatter for date fields
        if is_date_field(field.annotation):
            format_str = field_info.get("format", "YY[w]ww-E")
            column[":format"] = (
                f"value => value ? Quasar.date.formatDate(value, '{format_str}') : ''"
            )

        columns.append(column)

    # Sort columns by ui_order if specified
    def get_order(col_name: str) -> int:
        field = model_class.model_fields[col_name]
        sa_kwargs = getattr(field, "sa_column_kwargs", None)
        if isinstance(sa_kwargs, (PydanticUndefinedType, type(None))):
            return 999
        return sa_kwargs.get("info", {}).get("ui_order", 999)

    columns.sort(key=lambda col: get_order(col["name"]))

    # Add warning emoji column first if model has warning_emoji property
    if hasattr(model_class, "warning_emoji"):
        columns.insert(
            0,
            {
                "name": "warning_emoji",
                "label": "",
                "field": "warning_emoji",
            },
        )

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
    # Find primary key field
    primary_key_field = next(
        (
            name
            for name, field in model.__class__.model_fields.items()
            if getattr(field, "primary_key", False)
        ),
        None,
    )
    if not primary_key_field:
        raise ValueError(f"No primary key field found in model {model.__class__.__name__}")

    row = {"id": getattr(model, primary_key_field)}  # Use primary key for row key

    # Add warning emoji if model has it
    if hasattr(model, "warning_emoji"):
        row["warning_emoji"] = model.warning_emoji

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
