"""Tests for active potting lot service."""

from unittest.mock import Mock

from production_control.potting_lots.active_service import ActivePottingLotService
from production_control.potting_lots.models import PottingLot


def test_active_potting_lot_service_exists():
    """Test ActivePottingLotService exists."""
    assert ActivePottingLotService is not None


def test_service_initializes_with_empty_state():
    """Test service initializes with empty active lots."""
    mock_repository = Mock()
    service = ActivePottingLotService(mock_repository)

    assert service.get_active_lot_for_line(1) is None
    assert service.get_active_lot_for_line(2) is None


def test_service_activate_lot_basic():
    """Test service can activate a lot."""
    mock_repository = Mock()
    potting_lot = PottingLot(id=1001, naam="Test Plant", bollen_code=12345)
    mock_repository.get_by_id.return_value = potting_lot

    service = ActivePottingLotService(mock_repository)

    active_lot = service.activate_lot(1, 1001)

    assert active_lot.line == 1
    assert active_lot.potting_lot_id == 1001
    assert active_lot.potting_lot == potting_lot


def test_service_deactivate_lot():
    """Test service can deactivate a lot."""
    mock_repository = Mock()
    potting_lot = PottingLot(id=1001, naam="Test Plant", bollen_code=12345)
    mock_repository.get_by_id.return_value = potting_lot

    service = ActivePottingLotService(mock_repository)

    # First activate a lot
    service.activate_lot(1, 1001)
    assert service.get_active_lot_for_line(1) is not None

    # Then deactivate it
    result = service.deactivate_lot(1)

    assert result is True
    assert service.get_active_lot_for_line(1) is None
