"""Integration tests for OPC/UA potting line controller."""

import pytest
from production_control.potting_lots.line_controller import (
    PottingLineController,
)

pytestmark = pytest.mark.integration


@pytest.fixture
def controller():
    """Create controller instance for testing."""
    from production_control.config.opc_config import OPCConfig

    # Use test configuration
    test_config = OPCConfig(
        endpoint="opc.tcp://127.0.0.1:4840",  # uaserver default endpoint
        connection_timeout=5,
        retry_attempts=2,
        retry_delay=0.1,  # Faster retries for tests
    )

    return PottingLineController(config=test_config)


@pytest.mark.asyncio
async def test_set_and_get_active_lot(controller):
    """Test setting and getting active lot numbers with production-ready error handling."""
    # Test setting active lot on line 1 with automatic connection
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


@pytest.mark.asyncio
async def test_initialize_lines(controller):
    """Test concurrent line initialization with production-ready approach."""
    # Set some initial values
    await controller.set_active_lot(1, 999)
    await controller.set_active_lot(2, 888)

    # Initialize should reset both lines to 0 concurrently
    success = await controller.initialize_lines()
    assert success

    # Verify both lines are set to 0
    line1_active = await controller.get_active_lot(1)
    line2_active = await controller.get_active_lot(2)
    assert line1_active == 0
    assert line2_active == 0


@pytest.mark.asyncio
async def test_connection_failure():
    """Test behavior when OPC/UA server is not available with production error handling."""
    from production_control.config.opc_config import OPCConfig

    # Use invalid endpoint with test configuration
    test_config = OPCConfig(
        endpoint="opc.tcp://127.0.0.1:9999/invalid/",
        connection_timeout=1,  # Fast timeout for tests
        retry_attempts=2,
        retry_delay=0.1,
    )
    controller = PottingLineController(config=test_config)

    # Should fail to connect after retries
    success = await controller.get_active_lot(1)
    assert not success
    assert controller.last_error is not None

    # Operations should fail gracefully with proper error handling
    success = await controller.set_active_lot(1, 123)
    assert not success

    active_lot = await controller.get_active_lot(1)
    assert active_lot is None
