"""Tests for bulb picklist label generation."""

import os
import base64
from datetime import date
from unittest.mock import patch, MagicMock

import pytest

from production_control.bulb_picklist.models import BulbPickList


def test_label_generator_exists():
    """Test that the LabelGenerator class exists."""
    from production_control.bulb_picklist.label_generation import LabelGenerator

    assert LabelGenerator is not None


def test_label_generator_init_with_defaults():
    """Test that the LabelGenerator initializes with the template directory."""
    from production_control.bulb_picklist.label_generation import LabelGenerator

    generator = LabelGenerator()

    assert generator.template_dir is not None
    assert generator.template_dir.exists()
    assert (generator.template_dir / "base.html.jinja2").exists()
    assert (generator.template_dir / "labels.html.jinja2").exists()


def test_generate_label_html():
    """Test generating HTML for a label from a BulbPickList record."""
    from production_control.bulb_picklist.label_generation import LabelGenerator

    # Create a test record
    record = BulbPickList(
        id=41393,
        bollen_code=26647,
        ras="T.Double Dutch 13",
        locatie="3604.1000",
        aantal_bakken=12.0,
        aantal_bollen=100.0,
        oppot_datum=date(2023, 1, 2),
        oppot_week="23w01",
    )

    generator = LabelGenerator()
    html = generator.generate_label_html(record)

    # Check that the HTML contains the record values
    assert record.ras in html
    assert str(record.bollen_code) in html
    assert str(record.id) in html
    assert record.locatie in html
    assert str(int(record.aantal_bakken)) in html
    assert "kratten" in html
    assert record.oppot_week in html

    # Check that the default dimensions are used
    assert "151mm" in html
    assert "101mm" in html


def test_generate_label_html_with_custom_dimensions():
    """Test generating HTML for a label with custom dimensions."""
    from production_control.bulb_picklist.label_generation import LabelGenerator

    # Create a test record
    record = BulbPickList(
        id=41393,
        bollen_code=26647,
        ras="T.Double Dutch 13",
        locatie="3604.1000",
        aantal_bakken=12.0,
        aantal_bollen=100.0,
        oppot_datum=date(2023, 1, 2),
        oppot_week="23w01",
    )

    generator = LabelGenerator()
    custom_width = "100mm"
    custom_height = "75mm"
    html = generator.generate_label_html(record, width=custom_width, height=custom_height)

    # Check that the HTML contains the custom dimensions
    assert custom_width in html
    assert custom_height in html

    # Check that the page size is set correctly
    assert f"size: {custom_width} {custom_height}" in html

    # Check that the label dimensions are set correctly
    assert f"width: {custom_width}" in html
    assert f"height: {custom_height}" in html


def test_generate_qr_code():
    """Test generating a QR code for a BulbPickList record."""
    from production_control.bulb_picklist.label_generation import LabelGenerator

    # Create a test record
    record = BulbPickList(
        id=41393,
        bollen_code=26647,
        ras="T.Double Dutch 13",
        locatie="3604.1000",
        aantal_bakken=12.0,
        aantal_bollen=100.0,
        oppot_datum=date(2023, 1, 2),
    )

    generator = LabelGenerator()
    qr_code_data = generator.generate_qr_code(record)

    # Check that the QR code data is a base64 encoded string
    assert qr_code_data.startswith("data:image/png;base64,")

    # Verify we can decode the base64 data
    base64_data = qr_code_data.split(",")[1]
    decoded_data = base64.b64decode(base64_data)
    assert len(decoded_data) > 0


def test_generate_qr_code_with_base_url():
    """Test generating a QR code with a custom base URL."""
    from production_control.bulb_picklist.label_generation import LabelGenerator

    # Create a test record
    record = BulbPickList(
        id=41393,
        bollen_code=26647,
        ras="T.Double Dutch 13",
        locatie="3604.1000",
        aantal_bakken=12.0,
        aantal_bollen=100.0,
        oppot_datum=date(2023, 1, 2),
    )

    generator = LabelGenerator()
    base_url = "https://example.com"
    qr_code_data = generator.generate_qr_code(record, base_url=base_url)

    # Check that the QR code data is a base64 encoded string
    assert qr_code_data.startswith("data:image/png;base64,")

    # Verify we can decode the base64 data
    base64_data = qr_code_data.split(",")[1]
    decoded_data = base64.b64decode(base64_data)
    assert len(decoded_data) > 0

    # We can't directly check the URL in the QR code image,
    # but we can verify the method was called with the correct parameters


def test_qr_code_in_label_html():
    """Test that the QR code is included in the label HTML."""
    from production_control.bulb_picklist.label_generation import LabelGenerator

    # Create a test record
    record = BulbPickList(
        id=41393,
        bollen_code=26647,
        ras="T.Double Dutch 13",
        locatie="3604.1000",
        aantal_bakken=12.0,
        aantal_bollen=100.0,
        oppot_datum=date(2023, 1, 2),
        oppot_week="23w01",
    )

    generator = LabelGenerator()
    html = generator.generate_label_html(record)

    # Check that the HTML contains the QR code
    assert "qr-code" in html
    assert "data:image/png;base64," in html


@pytest.mark.parametrize("provide_output_path", [True, False])
def test_generate_pdf(provide_output_path, tmp_path):
    """Test generating a PDF from a BulbPickList record."""
    from production_control.bulb_picklist.label_generation import LabelGenerator

    # Create a test record
    record = BulbPickList(
        id=41393,
        bollen_code=26647,
        ras="T.Double Dutch 13",
        locatie="3604.1000",
        aantal_bakken=12.0,
        aantal_bollen=100.0,
        oppot_datum=date(2023, 1, 2),
        oppot_week="23w01",
    )

    generator = LabelGenerator()

    # Mock the HTML.write_pdf method to avoid actually generating a PDF
    with patch("production_control.bulb_picklist.label_generation.HTML") as mock_html:
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance

        if provide_output_path:
            output_path = os.path.join(tmp_path, "test_label.pdf")
            result = generator.generate_pdf(record, output_path)
            assert result == output_path
        else:
            result = generator.generate_pdf(record)
            assert result.endswith(".pdf")

        # Verify that HTML.write_pdf was called
        mock_html_instance.write_pdf.assert_called_once()


@pytest.mark.parametrize("provide_output_path", [True, False])
def test_generate_pdf_with_custom_dimensions(provide_output_path, tmp_path):
    """Test generating a PDF with custom dimensions."""
    from production_control.bulb_picklist.label_generation import LabelGenerator

    # Create a test record
    record = BulbPickList(
        id=41393,
        bollen_code=26647,
        ras="T.Double Dutch 13",
        locatie="3604.1000",
        aantal_bakken=12.0,
        aantal_bollen=100.0,
        oppot_datum=date(2023, 1, 2),
        oppot_week="23w01",
    )

    generator = LabelGenerator()
    custom_width = "100mm"
    custom_height = "75mm"

    # Mock the HTML.write_pdf method to avoid actually generating a PDF
    with patch("production_control.bulb_picklist.label_generation.HTML") as mock_html:
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance

        if provide_output_path:
            output_path = os.path.join(tmp_path, "test_label.pdf")
            result = generator.generate_pdf(
                record, output_path, width=custom_width, height=custom_height
            )
            assert result == output_path
        else:
            result = generator.generate_pdf(record, width=custom_width, height=custom_height)
            assert result.endswith(".pdf")

        # Verify that HTML.write_pdf was called
        mock_html_instance.write_pdf.assert_called_once()
