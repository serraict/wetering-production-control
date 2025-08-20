"""Tests for CLI configuration and infrastructure."""

import logging
from io import StringIO
from typing import Generator

import pytest
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock

from production_control.__cli__ import app


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def captured_logs() -> Generator[StringIO, None, None]:
    """Capture log output for testing."""
    log_output = StringIO()
    handler = logging.StreamHandler(log_output)
    logger = logging.getLogger("production_control")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    try:
        yield log_output
    finally:
        logger.removeHandler(handler)


def test_cli_logs_operations(cli_runner, captured_logs):
    """Test that CLI operations are properly logged."""
    # Run a command that should generate logs
    result = cli_runner.invoke(app, ["version"])
    assert result.exit_code == 0

    # Verify logs are generated and readable
    logs = captured_logs.getvalue()
    assert "Production Control" in logs
    assert "version" in logs


