"""Tests for potting lot URL parsing functionality."""

import pytest

from production_control.potting_lots.url_parser import (
    extract_lot_id_from_barcode,
    is_potting_lot_url,
)


class TestExtractLotIdFromBarcode:
    """Test cases for extracting lot ID from barcode text."""

    @pytest.mark.parametrize(
        "input_text,expected_id,description",
        [
            # Valid URLs and paths
            ("https://example.com/potting-lots/scan/12345", 12345, "full HTTPS URL"),
            ("http://localhost:8080/potting-lots/scan/98765", 98765, "full HTTP URL"),
            ("/potting-lots/scan/2021", 2021, "relative path"),
            ("https://vine.serraict.com/potting-lots/scan/1980", 1980, "Vine website URL"),
            ("https://example.com/potting-lots/scan/0", 0, "zero ID"),
            ("https://example.com/potting-lots/scan/999999", 999999, "large ID"),
            # Direct numeric IDs (fallback)
            ("123", 123, "direct numeric ID"),
            ("0", 0, "direct zero ID"),
            # URLs with extra content
            (
                "https://example.com/potting-lots/scan/123/extra/path",
                123,
                "URL with extra path segments",
            ),
            (
                "  https://example.com/potting-lots/scan/456  ",
                456,
                "URL with surrounding whitespace",
            ),
            (
                "https://example.com/potting-lots/scan/789?param=value",
                789,
                "URL with query parameters",
            ),
            ("https://example.com/potting-lots/scan/101#section", 101, "URL with fragment"),
        ],
    )
    def test_valid_extractions(self, input_text, expected_id, description):
        """Test valid lot ID extractions."""
        result = extract_lot_id_from_barcode(input_text)
        assert result == expected_id, f"Failed for {description}: {input_text}"

    @pytest.mark.parametrize(
        "input_text,description",
        [
            # Invalid URLs
            ("https://example.com/potting-lots/scan/", "URL with missing ID"),
            ("https://example.com/potting-lots/scan/abc", "URL with non-numeric ID"),
            ("https://example.com/other-page/scan/123", "URL with wrong path pattern"),
            ("https://example.com/potting-lots/scan/-5", "URL with negative ID"),
            # Invalid direct inputs
            ("-123", "direct negative ID"),
            ("123.45", "float-like string"),
            ("abc123", "mixed alphanumeric string"),
            ("not-a-url-at-all", "plain text that is not a URL"),
            # Edge cases
            ("", "empty string"),
            ("   ", "whitespace only string"),
            (None, "None input"),
            (123, "non-string input (integer)"),
        ],
    )
    def test_invalid_extractions(self, input_text, description):
        """Test cases that should return None."""
        result = extract_lot_id_from_barcode(input_text)
        assert result is None, f"Should return None for {description}: {input_text}"


class TestIsPottingLotUrl:
    """Test cases for checking if URL is a potting lot URL."""

    @pytest.mark.parametrize(
        "url,expected,description",
        [
            # Valid URLs
            ("https://example.com/potting-lots/scan/123", True, "valid full URL"),
            ("/potting-lots/scan/456", True, "valid relative path"),
            # Invalid URLs
            ("/other-path/scan/123", False, "invalid path pattern"),
            ("https://example.com/potting-lots/scan/", False, "URL with missing ID"),
            ("https://example.com/potting-lots/scan/abc", False, "URL with non-numeric ID"),
            # Edge cases
            ("", False, "empty string"),
            (None, False, "None input"),
            (123, False, "non-string input"),
        ],
    )
    def test_url_validation(self, url, expected, description):
        """Test URL validation with various inputs."""
        result = is_potting_lot_url(url)
        assert result is expected, f"Failed for {description}: {url}"
