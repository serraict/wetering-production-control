"""Tests for Jinja2 template rendering for bulb picklist labels."""

import pytest


def test_jinja2_dependencies():
    """Verify Jinja2 is available."""
    try:
        import jinja2

        assert jinja2 is not None
    except ImportError:
        pytest.fail("Jinja2 is not installed")


def test_jinja2_template_loader():
    """Test template loader initialization."""
    from pathlib import Path
    import jinja2
    from production_control.bulb_picklist.label_generation import LabelGenerator

    generator = LabelGenerator()

    # Check that the template loader is initialized
    assert generator.jinja_env is not None
    assert isinstance(generator.jinja_env, jinja2.Environment)

    # Check that the template loader can find our templates
    template_dir = (
        Path(__file__).parent.parent.parent
        / "src"
        / "production_control"
        / "bulb_picklist"
        / "templates"
    )
    assert template_dir.exists()
    assert (template_dir / "base.html.jinja2").exists()
    assert (template_dir / "labels.html.jinja2").exists()


def test_render_single_label_with_jinja():
    """Test rendering single label with Jinja2."""
    from datetime import date
    from production_control.bulb_picklist.models import BulbPickList
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
    html = generator.generate_labels_html(record)

    # Check that the HTML contains the record values
    assert record.ras in html
    assert str(record.bollen_code) in html
    assert str(record.id) in html
    assert record.locatie in html
    assert str(int(record.aantal_bakken)) in html
    assert "kratten" in html


def test_generate_multiple_labels():
    """Test generating PDF with multiple labels."""
    from datetime import date
    from production_control.bulb_picklist.models import BulbPickList
    from production_control.bulb_picklist.label_generation import LabelGenerator

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
        ),
        BulbPickList(
            id=41394,
            bollen_code=26648,
            ras="T.Single Red",
            locatie="3604.2000",
            aantal_bakken=8.0,
            aantal_bollen=80.0,
            oppot_datum=date(2023, 1, 3),
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
        assert str(int(record.aantal_bakken)) in html

    # Check that we have multiple labels
    assert html.count('<div class="label">') == len(records)


def test_generate_empty_labels():
    """Test handling empty record list."""
    from production_control.bulb_picklist.label_generation import LabelGenerator

    generator = LabelGenerator()
    html = generator.generate_labels_html([])

    # Check that we have no labels
    assert '<div class="label">' not in html
