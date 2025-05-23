"""Tests for potting lots label generation."""

import os
import tempfile
from datetime import date
from decimal import Decimal

import pytest

from production_control.potting_lots.models import PottingLot
from production_control.potting_lots.label_generation import LabelGenerator
from production_control.data.label_generation import LabelConfig


@pytest.fixture
def sample_potting_lot():
    """Create a sample potting lot for testing."""
    return PottingLot(
        id=1001,
        naam="Test Plant",
        bollen_code=12345,
        oppot_datum=date(2023, 1, 1),
        productgroep_code=42,
        bolmaat=16.5,
        bol_per_pot=3.0,
        rij_cont=4,
        olsthoorn_bollen_code="OBC123",
        aantal_pot=100,
        aantal_bol=300,
        aantal_containers_oppotten=Decimal("25.0"),
        water="Normal",
        fust="Standard",
        opmerking="Test remark",
    )


def test_label_config_initialization():
    """Test initializing LabelConfig."""
    config = LabelConfig(width="100mm", height="75mm", base_url="https://example.com")
    assert config.width == "100mm"
    assert config.height == "75mm"
    assert config.base_url == "https://example.com"


def test_label_config_from_env(monkeypatch):
    """Test creating LabelConfig from environment variables."""
    # Set environment variables
    monkeypatch.setenv("LABEL_WIDTH", "120mm")
    monkeypatch.setenv("LABEL_HEIGHT", "80mm")
    monkeypatch.setenv("QR_CODE_BASE_URL", "https://test.com")

    # Create config from environment
    config = LabelConfig.from_env()

    # Verify values
    assert config.width == "120mm"
    assert config.height == "80mm"
    assert config.base_url == "https://test.com"


def test_label_generator_initialization():
    """Test initializing LabelGenerator."""
    generator = LabelGenerator()
    assert generator is not None
    assert generator.template_dir.exists()
    assert (generator.template_dir / "labels.html.jinja2").exists()


def test_generate_qr_code(sample_potting_lot):
    """Test generating a QR code for a potting lot."""
    generator = LabelGenerator()
    qr_code = generator.generate_qr_code(sample_potting_lot)

    # Verify it's a data URL
    assert qr_code.startswith("data:image/png;base64,")

    # Verify it contains data
    assert len(qr_code) > 100


def test_prepare_record_data(sample_potting_lot):
    """Test preparing record data for template rendering."""
    generator = LabelGenerator()
    data = generator._prepare_record_data(sample_potting_lot, "https://example.com")

    # Verify basic fields
    assert data["id"] == sample_potting_lot.id
    assert data["bollen_code"] == sample_potting_lot.bollen_code
    assert data["naam"] == sample_potting_lot.naam
    assert "qr_code" in data
    assert data["scan_url"] == f"https://example.com/potting-lots/scan/{sample_potting_lot.id}"
    assert data["oppot_datum"]  # Should be formatted


def test_generate_labels_html(sample_potting_lot):
    """Test generating HTML for labels."""
    generator = LabelGenerator()
    config = LabelConfig(width="100mm", height="75mm")
    html = generator.generate_labels_html(sample_potting_lot, config)

    # Verify HTML contains expected elements
    assert "<!DOCTYPE html>" in html
    assert "<html>" in html
    assert sample_potting_lot.naam in html
    assert str(sample_potting_lot.id) in html
    assert str(sample_potting_lot.bollen_code) in html
    assert "data:image/png;base64," in html  # QR code


def test_generate_pdf(sample_potting_lot):
    """Test generating a PDF for a potting lot."""
    generator = LabelGenerator()
    config = LabelConfig()

    # Generate PDF to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        pdf_path = generator.generate_pdf(sample_potting_lot, config, tmp.name)

        # Verify file exists and has content
        assert os.path.exists(pdf_path)
        assert os.path.getsize(pdf_path) > 0

        # Clean up
        os.unlink(pdf_path)


def test_generate_duplicate_labels(sample_potting_lot):
    """Test that each potting lot gets two identical labels."""
    generator = LabelGenerator()
    config = LabelConfig(width="100mm", height="75mm")

    # Generate HTML for a single potting lot
    html = generator.generate_labels_html(sample_potting_lot, config)

    # Count occurrences of key elements that should appear once per label
    # The QR code data URL will be unique for each label instance
    qr_code_count = html.count("data:image/png;base64,")

    # Each potting lot should have two labels
    assert qr_code_count == 2

    # Check for other identifying information that should appear twice
    assert html.count(str(sample_potting_lot.id)) >= 2
    assert html.count(sample_potting_lot.naam) >= 2


def test_generate_multiple_duplicate_labels(sample_potting_lot):
    """Test generating duplicate labels for multiple records."""
    generator = LabelGenerator()
    config = LabelConfig(width="100mm", height="75mm")

    # Create a second potting lot
    second_lot = PottingLot(
        id=1002,
        naam="Another Plant",
        bollen_code=54321,
        oppot_datum=date(2023, 2, 1),
        productgroep_code=43,
        bolmaat=17.5,
        bol_per_pot=2.0,
        rij_cont=5,
        olsthoorn_bollen_code="OBC456",
        aantal_pot=200,
        aantal_bol=400,
        aantal_containers_oppotten=Decimal("50.0"),
        water="Extra",
        fust="Special",
        opmerking="Another test remark",
    )

    # Generate HTML for both potting lots
    html = generator.generate_labels_html([sample_potting_lot, second_lot], config)

    # Count occurrences of key elements
    qr_code_count = html.count("data:image/png;base64,")

    # Each potting lot should have two labels (total of 4)
    assert qr_code_count == 4

    # Check for identifying information from both records
    assert html.count(str(sample_potting_lot.id)) >= 2
    assert html.count(sample_potting_lot.naam) >= 2
    assert html.count(str(second_lot.id)) >= 2
    assert html.count(second_lot.naam) >= 2
