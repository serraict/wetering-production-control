"""Tests for bulb picklist label generation."""

import os
from datetime import date
from unittest.mock import patch, MagicMock

import pytest

from production_control.bulb_picklist.models import BulbPickList


def test_label_generator_exists():
    """Test that the LabelGenerator class exists."""
    from production_control.bulb_picklist.label_generation import LabelGenerator

    assert LabelGenerator is not None


def test_label_generator_init_with_defaults():
    """Test that the LabelGenerator initializes with the template path."""
    from production_control.bulb_picklist.label_generation import LabelGenerator

    generator = LabelGenerator()

    assert generator.template_dir is not None
    assert generator.template_path is not None
    assert generator.template_path.name == "label.html"
    assert generator.template_path.exists()


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
