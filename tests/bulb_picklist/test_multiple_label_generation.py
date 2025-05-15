"""Tests for generating multiple labels based on pallet count."""

from production_control.bulb_picklist.models import BulbPickList
from production_control.bulb_picklist.label_generation import LabelGenerator


def test_generate_multiple_pallet_labels():
    """Test generating multiple labels based on pallet count."""
    # Create a test record with multiple pallets
    record = BulbPickList(
        id=1,
        bollen_code=12345,
        ras="Test Variety",
        locatie="Test Location",
        aantal_bakken=68,  # This should result in 3 pallets
        aantal_bollen=1000,
        oppot_week="2025-W20",
    )

    # Create a label generator
    generator = LabelGenerator()

    # Generate HTML for the labels
    html_content = generator.generate_labels_html(record)

    # Check that the HTML contains pallet information
    assert "Pallet 1/3" in html_content
    assert "Pallet 2/3" in html_content
    assert "Pallet 3/3" in html_content

    # Skip PDF generation test for simplicity
    # This is already tested in test_pdf_label_generation.py
