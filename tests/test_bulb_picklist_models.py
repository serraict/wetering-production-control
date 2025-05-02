"""Tests for bulb picklist models."""

from datetime import date
from production_control.bulb_picklist.models import BulbPickList


def test_bulb_picklist_model_exists():
    """Test BulbPickList model exists."""
    assert BulbPickList is not None


def test_bulb_picklist_model_attributes():
    """Test BulbPickList model has expected attributes."""
    # Arrange
    test_date = date(2023, 1, 1)  # January 1, 2023 (week 52)

    # Act
    bulb_picklist = BulbPickList(
        id=1001,
        bollen_code=12345,
        ras="Test Bulb",
        locatie="A1-B2",
        aantal_bakken=10.5,
        aantal_bollen=100.0,
        oppot_datum=test_date,
    )

    # Assert
    assert bulb_picklist.id == 1001
    assert bulb_picklist.bollen_code == 12345
    assert bulb_picklist.ras == "Test Bulb"
    assert bulb_picklist.locatie == "A1-B2"
    assert bulb_picklist.aantal_bakken == 10.5
    assert bulb_picklist.aantal_bollen == 100.0
    assert bulb_picklist.oppot_datum == test_date


def test_bulb_picklist_primary_key():
    """Test that id is the primary key for BulbPickList model."""
    from sqlalchemy.inspection import inspect

    # Use SQLAlchemy's inspect to check the primary key
    primary_key_columns = [column.name for column in inspect(BulbPickList).primary_key]

    # Check that id is the primary key
    assert "id" in primary_key_columns

    # Check that bollen_code is not a primary key
    assert "bollen_code" not in primary_key_columns
