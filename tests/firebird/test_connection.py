"""Tests for Firebird connection module."""

import os
from unittest.mock import MagicMock, patch

import fdb

from production_control.firebird.connection import (
    execute_firebird_command,
    get_connection,
    get_firebird_config,
)


def test_get_firebird_config_defaults():
    """Test firebird config returns default values."""
    # Clear env vars
    for key in [
        "FIREBIRD_HOST",
        "FIREBIRD_PORT",
        "FIREBIRD_DATABASE",
        "FIREBIRD_USER",
        "FIREBIRD_PASSWORD",
    ]:
        os.environ.pop(key, None)

    config = get_firebird_config()

    assert config["host"] == "localhost"
    assert config["port"] == 3050
    assert config["database"] == "/firebird/data/production.fdb"
    assert config["user"] == "SYSDBA"
    assert config["password"] == "masterkey"


def test_get_firebird_config_from_env():
    """Test firebird config reads from environment variables."""
    os.environ["FIREBIRD_HOST"] = "firebird.example.com"
    os.environ["FIREBIRD_PORT"] = "3051"
    os.environ["FIREBIRD_DATABASE"] = "/data/custom.fdb"
    os.environ["FIREBIRD_USER"] = "testuser"
    os.environ["FIREBIRD_PASSWORD"] = "testpass"

    config = get_firebird_config()

    assert config["host"] == "firebird.example.com"
    assert config["port"] == 3051
    assert config["database"] == "/data/custom.fdb"
    assert config["user"] == "testuser"
    assert config["password"] == "testpass"

    # Cleanup
    for key in [
        "FIREBIRD_HOST",
        "FIREBIRD_PORT",
        "FIREBIRD_DATABASE",
        "FIREBIRD_USER",
        "FIREBIRD_PASSWORD",
    ]:
        os.environ.pop(key, None)


@patch("production_control.firebird.connection.fdb.connect")
def test_get_connection(mock_connect):
    """Test get_connection creates a database connection."""
    mock_conn = MagicMock()
    mock_connect.return_value = mock_conn

    conn = get_connection()

    assert conn == mock_conn
    mock_connect.assert_called_once()


@patch("production_control.firebird.connection.get_connection")
def test_execute_firebird_command_success(mock_get_connection):
    """Test successful SQL command execution."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    result = execute_firebird_command(
        "UPDATE TEELTPL SET AFW_AFLEV = ? WHERE TEELTNR = ?", (10, "24096")
    )

    assert result["success"] is True
    assert "successfully" in result["message"]
    mock_cursor.execute.assert_called_once_with(
        "UPDATE TEELTPL SET AFW_AFLEV = ? WHERE TEELTNR = ?", (10, "24096")
    )
    mock_conn.commit.assert_called_once()
    mock_cursor.close.assert_called_once()
    mock_conn.close.assert_called_once()


@patch("production_control.firebird.connection.get_connection")
def test_execute_firebird_command_without_params(mock_get_connection):
    """Test SQL command execution without parameters."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_get_connection.return_value = mock_conn

    result = execute_firebird_command("SELECT COUNT(*) FROM TEELTPL")

    assert result["success"] is True
    mock_cursor.execute.assert_called_once_with("SELECT COUNT(*) FROM TEELTPL")


@patch("production_control.firebird.connection.get_connection")
def test_execute_firebird_command_database_error(mock_get_connection):
    """Test error handling for database errors."""
    mock_get_connection.side_effect = fdb.DatabaseError("Connection failed")

    result = execute_firebird_command(
        "UPDATE TEELTPL SET AFW_AFLEV = ? WHERE TEELTNR = ?", (10, "24096")
    )

    assert result["success"] is False
    assert "Database error" in result["error"]
    assert "Connection failed" in result["error"]


@patch("production_control.firebird.connection.get_connection")
def test_execute_firebird_command_unexpected_error(mock_get_connection):
    """Test error handling for unexpected errors."""
    mock_get_connection.side_effect = ValueError("Unexpected error")

    result = execute_firebird_command(
        "UPDATE TEELTPL SET AFW_AFLEV = ? WHERE TEELTNR = ?", (10, "24096")
    )

    assert result["success"] is False
    assert "Unexpected error" in result["error"]
