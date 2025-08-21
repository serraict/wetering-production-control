"""Integration tests for OPC/UA potting line controller."""

import pytest

pytestmark = pytest.mark.integration

import asyncio
from unittest.mock import patch, MagicMock

from production_control.potting_lots.line_controller import (
    PottingLineController,
    ConnectionStatus,
)
from production_control.potting_lots.opc_test_server import PottingLineOPCTestServer


@pytest.fixture
async def test_server():
    """Start OPC/UA test server for integration tests."""
    server = PottingLineOPCTestServer()
    await server.start()
    # Small delay to ensure server is ready
    await asyncio.sleep(0.1)
    yield server
    await server.stop()


@pytest.fixture
def controller():
    """Create controller instance."""
    return PottingLineController()


@pytest.mark.asyncio
async def test_controller_connection(test_server, controller):
    """Test basic connection to OPC/UA server."""
    # Initially disconnected
    assert controller.status == ConnectionStatus.DISCONNECTED

    # Should connect successfully
    success = await controller.connect()
    assert success
    assert controller.status == ConnectionStatus.CONNECTED
    assert controller.last_error is None

    # Should disconnect cleanly
    await controller.disconnect()
    assert controller.status == ConnectionStatus.DISCONNECTED


@pytest.mark.asyncio
async def test_set_and_get_active_lot(test_server, controller):
    """Test setting and getting active lot numbers."""
    await controller.connect()

    # Test setting active lot on line 1
    success = await controller.set_active_lot(1, 123)
    assert success

    # Verify the value was set
    active_lot = await controller.get_active_lot(1)
    assert active_lot == 123

    # Test setting active lot on line 2
    success = await controller.set_active_lot(2, 456)
    assert success

    active_lot = await controller.get_active_lot(2)
    assert active_lot == 456

    # Test deactivation (setting to 0)
    success = await controller.set_active_lot(1, 0)
    assert success

    active_lot = await controller.get_active_lot(1)
    assert active_lot == 0

    await controller.disconnect()


@pytest.mark.asyncio
async def test_initialize_lines(test_server, controller):
    """Test line initialization."""
    # Set some initial values
    await controller.connect()
    await controller.set_active_lot(1, 999)
    await controller.set_active_lot(2, 888)
    await controller.disconnect()

    # Initialize should reset both lines to 0
    success = await controller.initialize_lines()
    assert success

    # Verify both lines are set to 0
    line1_active = await controller.get_active_lot(1)
    line2_active = await controller.get_active_lot(2)
    assert line1_active == 0
    assert line2_active == 0

    await controller.disconnect()


@pytest.mark.asyncio
async def test_connection_failure():
    """Test behavior when OPC/UA server is not available."""
    # Use invalid endpoint
    controller = PottingLineController("opc.tcp://127.0.0.1:9999/invalid/")

    # Should fail to connect
    success = await controller.connect()
    assert not success
    assert controller.status == ConnectionStatus.ERROR
    assert controller.last_error is not None

    # Operations should fail gracefully
    success = await controller.set_active_lot(1, 123)
    assert not success

    active_lot = await controller.get_active_lot(1)
    assert active_lot is None


@pytest.mark.asyncio
async def test_auto_reconnect(test_server, controller):
    """Test automatic reconnection attempts."""
    # Initially disconnected
    assert controller.status == ConnectionStatus.DISCONNECTED

    # set_active_lot should trigger connection attempt
    success = await controller.set_active_lot(1, 123)
    assert success
    assert controller.status == ConnectionStatus.CONNECTED

    # Verify the value was set
    active_lot = await controller.get_active_lot(1)
    assert active_lot == 123

    await controller.disconnect()


@pytest.mark.asyncio
async def test_get_status(controller):
    """Test status information retrieval."""
    status = controller.get_status()

    assert "status" in status
    assert "endpoint" in status
    assert "last_error" in status
    assert "last_connection_attempt" in status
    assert "connected_nodes" in status

    assert status["status"] == ConnectionStatus.DISCONNECTED.value
    assert status["endpoint"] == controller.endpoint
    assert status["connected_nodes"] == 0


class TestActiveServiceIntegration:
    """Tests for ActivePottingLotService integration with OPC/UA."""

    def test_service_initialization_with_controller(self):
        """Test that active service gets controller instance."""
        from production_control.potting_lots.repositories import PottingLotRepository
        from production_control.potting_lots.active_service import ActivePottingLotService

        repository = PottingLotRepository()
        service = ActivePottingLotService(repository)

        # Should have controller instance
        assert service._controller is not None
        assert hasattr(service._controller, "connect")
        assert hasattr(service._controller, "set_active_lot")

    @patch("production_control.potting_lots.active_service.run")
    def test_activation_triggers_controller_communication(self, mock_run):
        """Test that activating a lot triggers OPC/UA communication."""
        from production_control.potting_lots.repositories import PottingLotRepository
        from production_control.potting_lots.active_service import ActivePottingLotService
        from production_control.potting_lots.models import PottingLot

        # Mock repository with test data
        repository = PottingLotRepository()
        test_lot = PottingLot(
            id=123, naam="Test Lot", soort_id=1, klant_id=1, aantal_benodigde_potten=100
        )

        with patch.object(repository, "get_by_id", return_value=test_lot):
            service = ActivePottingLotService(repository)

            # Activate lot
            active_lot = service.activate_lot(line=1, potting_lot_id=123)

            # Verify activation
            assert active_lot is not None
            assert active_lot.line == 1
            assert active_lot.potting_lot_id == 123
            assert active_lot.potting_lot.naam == "Test Lot"

            # Verify OPC/UA communication was triggered
            mock_run.cpu_bound.assert_called_once()
            args = mock_run.cpu_bound.call_args[0]
            assert args[0] == service._send_activation_to_controller
            assert args[1] == 1  # line
            assert args[2] == 123  # lot_id

    @patch("production_control.potting_lots.active_service.run")
    def test_deactivation_triggers_controller_communication(self, mock_run):
        """Test that deactivating a lot triggers OPC/UA communication."""
        from production_control.potting_lots.repositories import PottingLotRepository
        from production_control.potting_lots.active_service import ActivePottingLotService
        from production_control.potting_lots.models import PottingLot

        # Setup service with active lot
        repository = PottingLotRepository()
        test_lot = PottingLot(
            id=123, naam="Test Lot", soort_id=1, klant_id=1, aantal_benodigde_potten=100
        )

        with patch.object(repository, "get_by_id", return_value=test_lot):
            service = ActivePottingLotService(repository)
            service.activate_lot(line=1, potting_lot_id=123)

            # Reset mock
            mock_run.reset_mock()

            # Deactivate lot
            success = service.deactivate_lot(line=1)

            # Verify deactivation
            assert success
            assert service.get_active_lot_for_line(1) is None

            # Verify OPC/UA communication was triggered
            mock_run.cpu_bound.assert_called_once()
            args = mock_run.cpu_bound.call_args[0]
            assert args[0] == service._send_activation_to_controller
            assert args[1] == 1  # line
            assert args[2] == 0  # lot_id (0 means deactivate)

    def test_controller_status_retrieval(self):
        """Test that service can retrieve controller status."""
        from production_control.potting_lots.repositories import PottingLotRepository
        from production_control.potting_lots.active_service import ActivePottingLotService

        repository = PottingLotRepository()
        service = ActivePottingLotService(repository)

        # Should be able to get status
        status = service.get_controller_status()
        assert isinstance(status, dict)
        assert "status" in status
        assert "endpoint" in status
