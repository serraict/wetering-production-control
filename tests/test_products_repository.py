"""Tests for product repository."""

import os
from unittest.mock import patch, MagicMock
import pytest
from sqlmodel import create_engine, Session, SQLModel
from production_control.products.models import (
    Product,
    ProductRepository,
    InvalidParameterError,
)


@pytest.fixture
def mock_engine():
    """Create a mock database engine."""
    engine = create_engine("dremio+flight://mock:32010/dremio")
    return engine


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def mock_products():
    """Create mock product data."""
    return [
        Product(
            id=1,
            name="Product 1",
            product_group_id=100,
            product_group_name="Group A",
        ),
        Product(
            id=2,
            name="Product 2",
            product_group_id=100,
            product_group_name="Group A",
        ),
        Product(
            id=3,
            name="Product 3",
            product_group_id=200,
            product_group_name="Group B",
        ),
    ]


@pytest.fixture
def repository(mock_engine):
    """Create a repository instance with a mock engine."""
    return ProductRepository(mock_engine)


def test_repository_init_with_connection_string():
    """Test repository initialization with connection string."""
    os.environ["VINEAPP_DB_CONNECTION"] = "dremio+flight://test:32010/dremio"
    repo = ProductRepository()
    assert str(repo.engine.url) == "dremio+flight://test:32010/dremio"


def test_repository_init_with_engine(mock_engine):
    """Test repository initialization with engine."""
    repo = ProductRepository(mock_engine)
    assert repo.engine == mock_engine


@patch("production_control.products.models.Session")
def test_get_all(mock_session_class, repository, mock_products):
    """Test get_all returns all products."""
    # Setup mock
    session = mock_session_class.return_value.__enter__.return_value
    session.execute.return_value = [(p,) for p in mock_products]

    # Execute
    result = repository.get_all()

    # Verify
    assert len(result) == 3
    assert all(isinstance(p, Product) for p in result)
    assert result[0].name == "Product 1"
    assert result[1].name == "Product 2"
    assert result[2].name == "Product 3"


@patch("production_control.products.models.Session")
def test_get_by_id(mock_session_class, repository, mock_products):
    """Test get_by_id returns correct product."""
    # Setup mock
    session = mock_session_class.return_value.__enter__.return_value
    session.exec.return_value.first.return_value = mock_products[0]

    # Execute
    result = repository.get_by_id(1)

    # Verify
    assert isinstance(result, Product)
    assert result.id == 1
    assert result.name == "Product 1"


@patch("production_control.products.models.Session")
def test_get_by_id_not_found(mock_session_class, repository):
    """Test get_by_id returns None when product not found."""
    # Setup mock
    session = mock_session_class.return_value.__enter__.return_value
    session.exec.return_value.first.return_value = None

    # Execute
    result = repository.get_by_id(999)

    # Verify
    assert result is None


@patch("production_control.products.models.Session")
def test_get_paginated(mock_session_class, repository, mock_products):
    """Test get_paginated returns correct page of products."""
    # Setup mock
    session = mock_session_class.return_value.__enter__.return_value
    
    # Mock count query
    count_result = MagicMock()
    count_result.one.return_value = 3
    session.exec.side_effect = [count_result, mock_products[:2]]

    # Execute
    products, total = repository.get_paginated(page=1, items_per_page=2)

    # Verify
    assert len(products) == 2
    assert total == 3
    assert products[0].name == "Product 1"
    assert products[1].name == "Product 2"


@patch("production_control.products.models.Session")
def test_get_paginated_with_filter(mock_session_class, repository, mock_products):
    """Test get_paginated with text filter."""
    # Setup mock
    session = mock_session_class.return_value.__enter__.return_value
    
    # Mock count query
    count_result = MagicMock()
    count_result.one.return_value = 1
    session.exec.side_effect = [count_result, [mock_products[0]]]

    # Execute
    products, total = repository.get_paginated(filter_text="Product 1")

    # Verify
    assert len(products) == 1
    assert total == 1
    assert products[0].name == "Product 1"


def test_get_paginated_invalid_page(repository):
    """Test get_paginated raises error for invalid page."""
    with pytest.raises(InvalidParameterError):
        repository.get_paginated(page=0)


def test_get_paginated_invalid_items_per_page(repository):
    """Test get_paginated raises error for invalid items_per_page."""
    with pytest.raises(InvalidParameterError):
        repository.get_paginated(items_per_page=0)
