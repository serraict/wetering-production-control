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
        bollen_code=12345,
        ras="Test Bulb",
        locatie="A1-B2",
        aantal_bakken=10.5,
        aantal_bollen=100.0,
        oppot_datum=test_date,
    )

    # Assert
    assert bulb_picklist.bollen_code == 12345
    assert bulb_picklist.ras == "Test Bulb"
    assert bulb_picklist.locatie == "A1-B2"
    assert bulb_picklist.aantal_bakken == 10.5
    assert bulb_picklist.aantal_bollen == 100.0
    assert bulb_picklist.oppot_datum == test_date


def test_bulb_picklist_oppot_week_calculation():
    """Test the oppot_week computed property."""
    # Test with date
    bulb_with_date = BulbPickList(
        bollen_code=12345,
        oppot_datum=date(2023, 1, 1),  # Week 52
    )
    assert bulb_with_date.oppot_week == 52

    # Test with different date
    bulb_with_different_date = BulbPickList(
        bollen_code=12345,
        oppot_datum=date(2023, 6, 15),  # Week 24
    )
    assert bulb_with_different_date.oppot_week == 24

    # Test without date
    bulb_without_date = BulbPickList(
        bollen_code=12345,
        oppot_datum=None,
    )
    assert bulb_without_date.oppot_week is None
