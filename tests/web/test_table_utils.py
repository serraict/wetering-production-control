"""Tests for table utilities."""

from datetime import date
from decimal import Decimal
from sqlmodel import SQLModel, Field

from production_control.web.components.table_utils import (
    get_table_columns,
    format_row,
    format_date,
)
from production_control.products.models import Product


def test_get_table_columns_generates_columns_from_model():
    """Test that get_table_columns generates correct column configuration from model metadata."""

    # Given
    class TestModel(SQLModel):
        id: int = Field(
            primary_key=True,
            title="ID",
            sa_column_kwargs={"info": {"ui_hidden": True}},
        )
        name: str = Field(
            title="Naam",
            description="Test name",
            sa_column_kwargs={"info": {"ui_sortable": True}},
        )
        group: str = Field(
            title="Groep",
            description="Test group",
            sa_column_kwargs={"info": {"ui_sortable": True}},
        )
        notes: str = Field(title="Notities")  # No ui_sortable

    # When
    columns = get_table_columns(TestModel)

    # Then - columns should appear in order of field definition
    assert columns == [
        {
            "name": "name",
            "label": "Naam",
            "field": "name",
            "sortable": True,
        },
        {
            "name": "group",
            "label": "Groep",
            "field": "group",
            "sortable": True,
        },
        {
            "name": "notes",
            "label": "Notities",
            "field": "notes",
        },
        {
            "name": "actions",
            "label": "Acties",
            "field": "actions",
        },
    ]


def test_get_table_columns_handles_missing_metadata():
    """Test that get_table_columns handles fields without metadata gracefully."""

    # Given
    class SimpleModel(SQLModel):
        id: int = Field()
        name: str = Field()

    # When
    columns = get_table_columns(SimpleModel)

    # Then - columns should appear in order of field definition
    assert columns == [
        {
            "name": "id",
            "label": "id",
            "field": "id",
        },
        {
            "name": "name",
            "label": "name",
            "field": "name",
        },
        {
            "name": "actions",
            "label": "Acties",
            "field": "actions",
        },
    ]


def test_get_table_columns_respects_hidden_fields():
    """Test that get_table_columns excludes fields marked as hidden."""

    # Given
    class ModelWithHidden(SQLModel):
        id: int = Field(sa_column_kwargs={"info": {"ui_hidden": True}})
        visible: str = Field(title="Visible")
        also_hidden: str = Field(sa_column_kwargs={"info": {"ui_hidden": True}})

    # When
    columns = get_table_columns(ModelWithHidden)

    # Then
    assert columns == [
        {
            "name": "visible",
            "label": "Visible",
            "field": "visible",
        },
        {
            "name": "actions",
            "label": "Acties",
            "field": "actions",
        },
    ]


def test_get_table_columns_generates_product_columns():
    """Test that get_table_columns generates correct columns from Product model."""
    # When
    columns = get_table_columns(Product)

    # Then
    assert columns == [
        {
            "name": "name",
            "label": "Naam",
            "field": "name",
            "sortable": True,
        },
        {
            "name": "product_group_name",
            "label": "Productgroep",
            "field": "product_group_name",
            "sortable": True,
        },
        {
            "name": "actions",
            "label": "Acties",
            "field": "actions",
        },
    ]


def test_format_row_respects_hidden_fields():
    """Test that format_row excludes fields marked as hidden."""

    # Given
    class ModelWithHidden(SQLModel):
        id: int = Field()
        visible: str = Field(title="Visible")
        hidden: str = Field(sa_column_kwargs={"info": {"ui_hidden": True}})

    model = ModelWithHidden(id=1, visible="Shown", hidden="Secret")

    # When
    row = format_row(model)

    # Then
    assert row == {
        "id": 1,
        "visible": "Shown",
    }
    assert "hidden" not in row


def test_format_date():
    """Test that format_date correctly formats dates using ISO week year."""
    # Given
    test_date = date(2024, 12, 30)  # Monday of week 1, 2025
    empty_date = None

    # When/Then
    assert format_date(test_date) == "25w01-1"  # ISO week year
    assert format_date(empty_date) == "--"  # Empty date handling


def test_format_row_with_dates():
    """Test that format_row correctly formats date fields."""

    # Given
    class ModelWithDates(SQLModel):
        id: int = Field(primary_key=True)
        name: str = Field()
        created_at: date = Field()

    model = ModelWithDates(
        id=1,
        name="Test",
        created_at=date(2024, 12, 30),  # Monday of week 1, 2025
    )

    # When
    row = format_row(model)

    # Then
    assert row == {
        "id": 1,
        "name": "Test",
        "created_at": "25w01-1",  # Date should be formatted
    }


def test_get_table_columns_with_dates():
    """Test that get_table_columns handles date fields correctly."""

    # Given
    class ModelWithDates(SQLModel):
        id: int = Field()
        created_at: date = Field(title="Created")

    # When
    columns = get_table_columns(ModelWithDates)

    # Then
    date_col = next(col for col in columns if col["name"] == "created_at")
    assert date_col == {
        "name": "created_at",
        "label": "Created",
        "field": "created_at",
    }


def test_get_table_columns_formats_decimals():
    """Test that get_table_columns adds decimal formatting."""

    # Given
    class ModelWithDecimals(SQLModel):
        id: int = Field()
        default_decimal: Decimal = Field(
            title="Default Format",
        )
        custom_decimal: Decimal = Field(
            title="Custom Format",
            sa_column_kwargs={
                "info": {
                    "decimals": 2,
                }
            },
        )

    # When
    columns = get_table_columns(ModelWithDecimals)

    # Then
    default_col = next(col for col in columns if col["name"] == "default_decimal")
    custom_col = next(col for col in columns if col["name"] == "custom_decimal")

    assert default_col[":format"] == "value => Number(value).toFixed(1)"  # Default 1 decimal
    assert custom_col[":format"] == "value => Number(value).toFixed(2)"  # Custom 2 decimals
