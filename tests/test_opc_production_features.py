"""Tests for production-ready OPC/UA features."""

import pytest
import asyncio
from unittest.mock import Mock, patch
from production_control.potting_lots.line_controller import (
    PottingLineController,
    ConnectionStatus,
    get_controller,
    shutdown_controller,
)
from production_control.config.opc_config import OPCConfig, get_opc_config


class TestOPCConfiguration:
    """Test OPC configuration management."""

    def test_default_config_loading(self):
        """Test that default configuration loads correctly."""
        config = get_opc_config()
        assert isinstance(config, OPCConfig)
        assert config.endpoint.startswith("opc.tcp://")
        assert config.retry_attempts > 0
        assert config.connection_timeout > 0

    def test_controller_uses_configuration(self):
        """Test that controller uses configuration correctly."""
        test_config = OPCConfig(
            endpoint="opc.tcp://test.example.com:4840", connection_timeout=20, retry_attempts=5
        )

        controller = PottingLineController(config=test_config)

        assert controller.endpoint == "opc.tcp://test.example.com:4840"
        assert controller.connection_timeout == 20
        assert controller.retry_attempts == 5

    def test_environment_override(self, monkeypatch):
        """Test that environment variables override configuration."""
        monkeypatch.setenv("OPC_ENDPOINT", "opc.tcp://env.example.com:4840")
        monkeypatch.setenv("OPC_RETRY_ATTEMPTS", "10")

        # Force config reload
        from production_control.config.opc_config import _config_manager

        if _config_manager:
            _config_manager._config = None

        config = get_opc_config()
        assert config.endpoint == "opc.tcp://env.example.com:4840"
        assert config.retry_attempts == 10


class TestProductionErrorHandling:
    """Test production-ready error handling."""

    @pytest.mark.asyncio
    async def test_retry_logic_on_timeout(self):
        """Test that operations retry on timeout errors."""
        test_config = OPCConfig(
            endpoint="opc.tcp://127.0.0.1:9999",  # Invalid endpoint
            retry_attempts=3,
            retry_delay=0.1,
            connection_timeout=1,
        )

        controller = PottingLineController(config=test_config)

        # Should fail after configured retry attempts
        success = await controller.set_active_lot(1, 123)
        assert not success
        assert controller.last_error is not None

    @pytest.mark.asyncio
    async def test_graceful_degradation(self):
        """Test that system works when OPC communication fails."""
        # This would be tested with a mock or by shutting down the OPC server
        # For now, just test that errors are handled gracefully

        test_config = OPCConfig(
            endpoint="opc.tcp://127.0.0.1:9999",  # Invalid endpoint
            retry_attempts=1,
            retry_delay=0.1,
        )

        controller = PottingLineController(config=test_config)

        # Operations should return False instead of raising exceptions
        success = await controller.set_active_lot(1, 123)
        assert success is False  # Explicit False, not exception

        value = await controller.get_active_lot(1)
        assert value is None  # Explicit None, not exception


class TestOPCConnectionManagement:
    """Test OPC connection lifecycle and management."""

    @pytest.mark.asyncio
    async def test_connection_status_tracking(self):
        """Test that connection status is tracked correctly."""
        test_config = OPCConfig(
            endpoint="opc.tcp://127.0.0.1:9999",  # Invalid for testing
            retry_attempts=1,
            connection_timeout=1,
        )

        controller = PottingLineController(config=test_config)

        # Initially disconnected
        assert controller.status == ConnectionStatus.DISCONNECTED

        # Try to connect (should fail)
        success = await controller.connect()
        assert not success
        assert controller.status == ConnectionStatus.ERROR
        assert controller.last_error is not None
        assert controller.last_connection_attempt is not None

    def test_status_information(self):
        """Test that status information is comprehensive."""
        controller = PottingLineController()
        status = controller.get_status()

        # Should have all expected fields
        expected_fields = [
            "status",
            "endpoint",
            "last_error",
            "last_connection_attempt",
            "cached_node_ids",
            "connection_timeout",
            "watchdog_interval",
            "retry_attempts",
        ]

        for field in expected_fields:
            assert field in status, f"Missing status field: {field}"

        # Status should be string representation
        assert isinstance(status["status"], str)
        assert status["cached_node_ids"] == 3  # line1, line2, last_updated

    @pytest.mark.asyncio
    async def test_global_controller_management(self):
        """Test global controller instance management."""
        # Clear any existing controller
        await shutdown_controller()

        # Get controller should create new instance
        controller1 = get_controller()
        controller2 = get_controller()

        # Should be the same instance
        assert controller1 is controller2

        # Should have default configuration
        assert controller1.endpoint.startswith("opc.tcp://")

        # Cleanup
        await shutdown_controller()


@pytest.mark.asyncio
async def test_concurrent_operations():
    """Test that concurrent OPC operations work correctly."""
    test_config = OPCConfig(
        endpoint="opc.tcp://127.0.0.1:9999",  # Invalid for testing
        retry_attempts=1,
        retry_delay=0.1,
        connection_timeout=1,
    )

    controller = PottingLineController(config=test_config)

    # Test concurrent operations (should all fail gracefully)
    tasks = [
        controller.set_active_lot(1, 100),
        controller.set_active_lot(2, 200),
        controller.get_active_lot(1),
        controller.get_active_lot(2),
        controller.initialize_lines(),
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # All should complete without exceptions
    for result in results:
        assert not isinstance(result, Exception), f"Unexpected exception: {result}"

    # Writes should return False, reads should return None, init should return False
    assert results[0] is False  # set_active_lot(1, 100)
    assert results[1] is False  # set_active_lot(2, 200)
    assert results[2] is None  # get_active_lot(1)
    assert results[3] is None  # get_active_lot(2)
    assert results[4] is False  # initialize_lines()


class TestPerformanceOptimizations:
    """Test performance optimizations."""

    def test_node_id_caching(self):
        """Test that NodeIds are cached for performance."""
        controller = PottingLineController()

        # Should have cached NodeIds instead of path-based lookup
        assert len(controller._node_ids) == 3
        assert "line1_active" in controller._node_ids
        assert "line2_active" in controller._node_ids
        assert "last_updated" in controller._node_ids

        # NodeIds should be proper AsyncUA NodeId objects
        from asyncua import ua

        for node_id in controller._node_ids.values():
            assert isinstance(node_id, ua.NodeId)

    def test_timeout_configuration(self):
        """Test that timeouts are properly configured."""
        test_config = OPCConfig(connection_timeout=15, watchdog_interval=45)

        controller = PottingLineController(config=test_config)

        # Client should be configured with appropriate timeouts (in milliseconds)
        assert controller.client.request_timeout == 15000  # 15 seconds -> 15000 ms
        assert controller.client.secure_channel_timeout == 45000  # 45 seconds -> 45000 ms
