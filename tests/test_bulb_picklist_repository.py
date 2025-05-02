"""Tests for bulb picklist repository."""

import pytest
from sqlmodel import create_engine, select
from production_control.bulb_picklist.models import BulbPickList
from production_control.bulb_picklist.repositories import BulbPickListRepository


@pytest.fixture
def mock_engine():
    """Create a mock database engine."""
    engine = create_engine("dremio+flight://mock:32010/dremio")
    return engine


def test_bulb_picklist_repository_initialization():
    """Test initializing the BulbPickListRepository."""
    repository = BulbPickListRepository()
    assert repository is not None


def test_bulb_picklist_repository_with_connection(mock_engine):
    """Test initializing the BulbPickListRepository with a connection."""
    repository = BulbPickListRepository(mock_engine)
    assert repository is not None


def test_bulb_picklist_repository_default_sorting():
    """Test the default sorting behavior of the repository."""
    repository = BulbPickListRepository()
    # We can verify the repository has the expected search fields
    assert repository.search_fields == ["id", "bollen_code", "ras", "locatie"]

    # We call _apply_default_sorting but don't need to use the result
    # This at least verifies the method doesn't raise exceptions
    repository._apply_default_sorting(select(BulbPickList))


def test_bulb_picklist_repository_filtering():
    """Test the filtering behavior of the repository."""
    # This test verifies that the repository has the correct search fields
    # for filtering bulb picklist records
    repository = BulbPickListRepository()
    assert "id" in repository.search_fields
    assert "bollen_code" in repository.search_fields
    assert "ras" in repository.search_fields
    assert "locatie" in repository.search_fields
