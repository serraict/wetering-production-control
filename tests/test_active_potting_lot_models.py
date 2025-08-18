"""Tests for active potting lot models."""

import pytest
from pydantic import ValidationError

from production_control.potting_lots.active_models import ActivePottingLot
from production_control.potting_lots.models import PottingLot


def test_active_potting_lot_model_exists():
    """Test ActivePottingLot model exists."""
    assert ActivePottingLot is not None


def test_active_potting_lot_model_basic_attributes():
    """Test ActivePottingLot model has expected attributes."""
    potting_lot = PottingLot(id=1001, naam="Test Plant", bollen_code=12345)

    active_lot = ActivePottingLot(line=1, potting_lot_id=1001, potting_lot=potting_lot)

    assert active_lot.line == 1
    assert active_lot.potting_lot_id == 1001
    assert active_lot.potting_lot == potting_lot


def test_active_potting_lot_model_validation():
    """Test ActivePottingLot model validates line numbers."""
    potting_lot = PottingLot(id=1001, naam="Test Plant", bollen_code=12345)

    # Valid line numbers should work
    ActivePottingLot(line=1, potting_lot_id=1001, potting_lot=potting_lot)
    ActivePottingLot(line=2, potting_lot_id=1001, potting_lot=potting_lot)

    # Invalid line numbers should raise ValidationError
    with pytest.raises(ValidationError):
        ActivePottingLot(line=0, potting_lot_id=1001, potting_lot=potting_lot)

    with pytest.raises(ValidationError):
        ActivePottingLot(line=3, potting_lot_id=1001, potting_lot=potting_lot)
