"""Tests for pagination state management."""

from production_control.web.components.pagination import Pagination


def test_pagination_defaults():
    """Test that Pagination has sensible defaults."""
    pagination = Pagination()
    assert pagination.page == 1
    assert pagination.rows_per_page == 10
    assert pagination.total_rows == 0
    assert pagination.sort_by is None
    assert pagination.descending is False


def test_pagination_from_dict():
    """Test that Pagination can be created from dictionary."""
    data = {
        "page": 2,
        "rowsPerPage": 20,
        "rowsNumber": 100,
        "sortBy": "name",
        "descending": True,
    }
    pagination = Pagination.from_dict(data)
    assert pagination.page == 2
    assert pagination.rows_per_page == 20
    assert pagination.total_rows == 100
    assert pagination.sort_by == "name"
    assert pagination.descending is True


def test_pagination_to_dict():
    """Test that Pagination can be converted to dictionary."""
    pagination = Pagination(
        page=2,
        rows_per_page=20,
        total_rows=100,
        sort_by="name",
        descending=True,
    )
    data = pagination.to_dict()
    assert data == {
        "page": 2,
        "rowsPerPage": 20,
        "rowsNumber": 100,
        "sortBy": "name",
        "descending": True,
    }


def test_pagination_update():
    """Test that Pagination can be updated from dictionary."""
    pagination = Pagination()
    data = {
        "page": 2,
        "rowsPerPage": 20,
        "rowsNumber": 100,
        "sortBy": "name",
        "descending": True,
    }
    pagination.update(data)
    assert pagination.page == 2
    assert pagination.rows_per_page == 20
    assert pagination.total_rows == 100
    assert pagination.sort_by == "name"
    assert pagination.descending is True
