"""Tests for bulb picklist label generation."""

import os
import base64
from datetime import date
from unittest.mock import patch, MagicMock

import pytest

from production_control.bulb_picklist.models import BulbPickList
from production_control.bulb_picklist.label_generation import LabelGenerator, LabelConfig


def test_label_config_default_values():
    """Test that LabelConfig initializes with default values."""
    config = LabelConfig()

    assert config.width == "151mm"
    assert config.height == "101mm"
    assert config.base_url == ""


def test_label_config_custom_values():
    """Test that LabelConfig initializes with custom values."""
    config = LabelConfig(
        width="100mm",
        height="75mm",
        base_url="https://example.com",
    )

    assert config.width == "100mm"
    assert config.height == "75mm"
    assert config.base_url == "https://example.com"


@patch.dict(
    os.environ,
    {
        "LABEL_WIDTH": "200mm",
        "LABEL_HEIGHT": "150mm",
        "QR_CODE_BASE_URL": "https://test.com",
    },
)
def test_label_config_from_env():
    """Test that LabelConfig.from_env reads values from environment variables."""
    config = LabelConfig.from_env()

    assert config.width == "200mm"
    assert config.height == "150mm"
    assert config.base_url == "https://test.com"


def test_label_generator_exists():
    """Test that the LabelGenerator class exists."""
    assert LabelGenerator is not None


def test_label_generator_init_with_defaults():
    """Test that the LabelGenerator initializes with the template directory."""
    from production_control.bulb_picklist.label_generation import LabelGenerator

    generator = LabelGenerator()

    assert generator.template_dir is not None
    assert generator.template_dir.exists()
    assert (generator.template_dir / "base.html.jinja2").exists()
    assert (generator.template_dir / "labels.html.jinja2").exists()


def test_generate_labels_html_single_record():
    """Test generating HTML for a single label."""
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
    html = generator.generate_labels_html(record)

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


def test_generate_labels_html_multiple_records():
    """Test generating HTML for multiple labels."""
    # Create test records
    records = [
        BulbPickList(
            id=41393,
            bollen_code=26647,
            ras="T.Double Dutch 13",
            locatie="3604.1000",
            aantal_bakken=12.0,
            aantal_bollen=100.0,
            oppot_datum=date(2023, 1, 2),
            oppot_week="23w01",
        ),
        BulbPickList(
            id=41394,
            bollen_code=26648,
            ras="T.Single Red",
            locatie="3604.2000",
            aantal_bakken=8.0,
            aantal_bollen=80.0,
            oppot_datum=date(2023, 1, 3),
            oppot_week="23w01",
        ),
    ]

    generator = LabelGenerator()
    html = generator.generate_labels_html(records)

    # Check that the HTML contains all record values
    for record in records:
        assert record.ras in html
        assert str(record.bollen_code) in html
        assert str(record.id) in html
        assert record.locatie in html


def test_generate_labels_html_with_custom_config():
    """Test generating HTML for labels with custom configuration."""
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
    config = LabelConfig(width="100mm", height="75mm", base_url="https://example.com")
    html = generator.generate_labels_html(record, config)

    # Check that the HTML contains the custom dimensions
    assert config.width in html
    assert config.height in html

    # Check that the page size is set correctly
    assert f"size: {config.width} {config.height}" in html

    # Check that the label dimensions are set correctly
    assert f"width: {config.width}" in html
    assert f"height: {config.height}" in html


def test_generate_labels_html_empty_records():
    """Test generating HTML with no records."""
    generator = LabelGenerator()
    html = generator.generate_labels_html([])

    # Check that we get a valid HTML document with no records
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html
    assert "records=[]" not in html  # This would be in the Python code, not the HTML


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
    html = generator.generate_labels_html(record)

    # Check that the HTML contains the QR code
    assert "qr-code" in html
    assert "data:image/png;base64," in html


@pytest.mark.parametrize("provide_output_path", [True, False])
def test_generate_pdf_single_record(provide_output_path, tmp_path):
    """Test generating a PDF from a single BulbPickList record."""
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
            result = generator.generate_pdf(record, output_path=output_path)
            assert result == output_path
        else:
            result = generator.generate_pdf(record)
            assert result.endswith(".pdf")

        # Verify that HTML.write_pdf was called
        mock_html_instance.write_pdf.assert_called_once()


@pytest.mark.parametrize("provide_output_path", [True, False])
def test_generate_pdf_multiple_records(provide_output_path, tmp_path):
    """Test generating a PDF from multiple BulbPickList records."""
    # Create test records
    records = [
        BulbPickList(
            id=41393,
            bollen_code=26647,
            ras="T.Double Dutch 13",
            locatie="3604.1000",
            aantal_bakken=12.0,
            aantal_bollen=100.0,
            oppot_datum=date(2023, 1, 2),
            oppot_week="23w01",
        ),
        BulbPickList(
            id=41394,
            bollen_code=26648,
            ras="T.Single Red",
            locatie="3604.2000",
            aantal_bakken=8.0,
            aantal_bollen=80.0,
            oppot_datum=date(2023, 1, 3),
            oppot_week="23w01",
        ),
    ]

    generator = LabelGenerator()

    # Mock the HTML.write_pdf method to avoid actually generating a PDF
    with patch("production_control.bulb_picklist.label_generation.HTML") as mock_html:
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance

        if provide_output_path:
            output_path = os.path.join(tmp_path, "test_labels.pdf")
            result = generator.generate_pdf(records, output_path=output_path)
            assert result == output_path
        else:
            result = generator.generate_pdf(records)
            assert result.endswith(".pdf")

        # Verify that HTML.write_pdf was called
        mock_html_instance.write_pdf.assert_called_once()


def test_generate_pdf_with_custom_config(tmp_path):
    """Test generating a PDF with custom configuration."""
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
    config = LabelConfig(width="100mm", height="75mm", base_url="https://example.com")

    # Mock the HTML.write_pdf method to avoid actually generating a PDF
    with patch("production_control.bulb_picklist.label_generation.HTML") as mock_html:
        mock_html_instance = MagicMock()
        mock_html.return_value = mock_html_instance

        output_path = os.path.join(tmp_path, "test_label.pdf")
        result = generator.generate_pdf(record, config=config, output_path=output_path)
        assert result == output_path

        # Verify that HTML.write_pdf was called
        mock_html_instance.write_pdf.assert_called_once()


def test_cleanup_pdf():
    """Test the cleanup_pdf method."""
    generator = LabelGenerator()
    pdf_path = "/tmp/test.pdf"
    delay = 10

    # Mock the ui.timer function
    with patch("nicegui.ui.timer") as mock_timer:
        generator.cleanup_pdf(pdf_path, delay)

        # Verify that ui.timer was called with the correct parameters
        mock_timer.assert_called_once()
        args, kwargs = mock_timer.call_args
        assert args[0] == delay  # First arg should be the delay
        assert kwargs.get("once") is True  # once parameter should be True
