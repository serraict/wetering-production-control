"""Tests for product models."""

from production_control.products.models import Product


def test_product_model_attributes():
    """Test Product model has expected attributes."""
    product = Product(
        id=1,
        name="Test Product",
        product_group_id=100,
        product_group_name="Test Group",
    )
    assert product.id == 1
    assert product.name == "Test Product"
    assert product.product_group_id == 100
    assert product.product_group_name == "Test Group"


def test_product_model_tablename():
    """Test Product model has correct table name."""
    assert Product.__tablename__ == "products"
    assert Product.__table_args__["schema"] == "Vines"
