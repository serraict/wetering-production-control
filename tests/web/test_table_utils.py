"""Tests for table utilities."""

from sqlmodel import SQLModel, Field

from production_control.web.components.table_utils import get_table_columns, format_row
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
            sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 1}},
        )
        group: str = Field(
            title="Groep",
            description="Test group",
            sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 2}},
        )
        notes: str = Field(title="Notities")  # No ui_sortable or ui_order

    # When
    columns = get_table_columns(TestModel)

    # Then
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

    # Then
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
