"""Tests for product models."""

import pytest
from production_control.products.models import (
    Product,
    RepositoryError,
    InvalidParameterError,
)


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


def test_repository_error():
    """Test RepositoryError can be raised."""
    with pytest.raises(RepositoryError) as exc_info:
        raise RepositoryError("Test error")
    assert str(exc_info.value) == "Test error"


def test_invalid_parameter_error():
    """Test InvalidParameterError can be raised and inherits from RepositoryError."""
    with pytest.raises(InvalidParameterError) as exc_info:
        raise InvalidParameterError("Invalid parameter")
    assert str(exc_info.value) == "Invalid parameter"
    assert isinstance(exc_info.value, RepositoryError)
