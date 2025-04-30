"""Tests for the Dremio query CLI tool."""

import pytest
from unittest.mock import patch

# Import the module directly
import dremio_query


class TestDremioQuery:
    """Tests for the Dremio query CLI tool."""

    def test_parse_connection_string_with_grpc(self):
        """Test parsing a connection string with grpc protocol."""
        connection_string = "grpc://user:pass@localhost:32010"
        result = dremio_query.parse_connection_string(connection_string)

        assert result["username"] == "user"
        assert result["password"] == "pass"
        assert result["arrow_endpoint"] == "grpc://localhost:32010"

    def test_parse_connection_string_with_tls(self):
        """Test parsing a connection string with grpc+tls protocol."""
        connection_string = "grpc+tls://user:pass@localhost:32010"
        result = dremio_query.parse_connection_string(connection_string)

        assert result["username"] == "user"
        assert result["password"] == "pass"
        assert result["arrow_endpoint"] == "grpc+tls://localhost:32010"

    def test_parse_connection_string_error(self):
        """Test error handling in parse_connection_string."""
        with pytest.raises(ValueError, match="Invalid connection string format"):
            dremio_query.parse_connection_string("invalid_string")

    @patch("os.getenv")
    def test_get_connection_missing_env_var(self, mock_getenv):
        """Test get_connection with missing environment variable."""
        # Configure mock to return None for SIMPLE_QUERY_CONNECTION
        mock_getenv.return_value = None

        with pytest.raises(
            ValueError, match="SIMPLE_QUERY_CONNECTION environment variable not set"
        ):
            dremio_query.get_connection()

        # Verify getenv was called with the correct argument
        mock_getenv.assert_called_once_with("SIMPLE_QUERY_CONNECTION")
