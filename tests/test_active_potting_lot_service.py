"""Tests for active potting lot service."""

from unittest.mock import Mock, patch

from production_control.potting_lots.active_service import ActivePottingLotService
from production_control.potting_lots.models import PottingLot


def test_active_potting_lot_service_exists():
    """Test ActivePottingLotService exists."""
    assert ActivePottingLotService is not None


def test_service_initializes_with_empty_state():
    """Test service initializes with empty active lots."""
    service = ActivePottingLotService()

    assert service.get_active_lot_for_line(1) is None
    assert service.get_active_lot_for_line(2) is None


@patch("production_control.potting_lots.active_service.PottingLotRepository")
def test_service_activate_lot_basic(mock_repo_class):
    """Test service can activate a lot."""
    # Setup mock repository and lot
    mock_repo = Mock()
    mock_repo_class.return_value = mock_repo
    potting_lot = PottingLot(id=123, naam="Test Plant", bollen_code=456)
    mock_repo.get_by_id.return_value = potting_lot

    service = ActivePottingLotService()

    # Test activation
    active_lot = service.activate_lot(1, 123)

    # Verify the lot was activated
    assert active_lot is not None
    assert active_lot.potting_lot_id == 123
    assert active_lot.line == 1
    assert service.get_active_lot_for_line(1) == active_lot

    # Verify repository was called correctly
    mock_repo.get_by_id.assert_called_once_with(123)


@patch("production_control.potting_lots.active_service.PottingLotRepository")
def test_service_deactivate_lot(mock_repo_class):
    """Test service can deactivate a lot."""
    # Setup mock repository and lot
    mock_repo = Mock()
    mock_repo_class.return_value = mock_repo
    potting_lot = PottingLot(id=123, naam="Test Plant", bollen_code=456)
    mock_repo.get_by_id.return_value = potting_lot

    service = ActivePottingLotService()

    # First activate a lot
    service.activate_lot(1, 123)
    assert service.get_active_lot_for_line(1) is not None

    # Then deactivate it
    result = service.deactivate_lot(1)

    assert result is True
    assert service.get_active_lot_for_line(1) is None


def test_deactivate_nonexistent_lot():
    """Test deactivating a lot that doesn't exist."""
    service = ActivePottingLotService()

    result = service.deactivate_lot(1)
    assert result is False
    assert service.get_active_lot_for_line(1) is None


@patch("production_control.potting_lots.active_service.PottingLotRepository")
def test_complete_lot_success(mock_repo_class):
    """Test successfully completing an active lot."""
    # Setup mock repository and lot
    mock_repo = Mock()
    mock_repo_class.return_value = mock_repo
    potting_lot = PottingLot(id=123, naam="Test Plant", bollen_code=456)
    mock_repo.get_by_id.return_value = potting_lot

    service = ActivePottingLotService()

    # First activate a lot
    service.activate_lot(1, 123)

    # Complete the lot
    result = service.complete_lot(1, 150)

    assert result is True
    # Verify lot is automatically deactivated after completion
    assert service.get_active_lot_for_line(1) is None


def test_complete_lot_no_active_lot():
    """Test completing when no lot is active."""
    service = ActivePottingLotService()

    result = service.complete_lot(1, 150)
    assert result is False


@patch("production_control.potting_lots.active_service.PottingLotRepository")
def test_complete_lot_with_zero_pots(mock_repo_class):
    """Test completing with zero pot count."""
    # Setup mock repository and lot
    mock_repo = Mock()
    mock_repo_class.return_value = mock_repo
    potting_lot = PottingLot(id=123, naam="Test Plant", bollen_code=456)
    mock_repo.get_by_id.return_value = potting_lot

    service = ActivePottingLotService()

    # First activate a lot
    service.activate_lot(1, 123)

    # Complete with zero pots - should still succeed (validation is at UI level)
    result = service.complete_lot(1, 0)

    assert result is True
    # Verify lot is deactivated
    assert service.get_active_lot_for_line(1) is None
