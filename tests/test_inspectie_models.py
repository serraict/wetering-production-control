"""Tests for inspectie models."""

from datetime import date

from production_control.inspectie.models import InspectieRonde


def test_inspectie_ronde_model_exists():
    """Test that InspectieRonde model can be instantiated."""
    record = InspectieRonde()
    assert record is not None


def test_inspectie_ronde_model_creation():
    """Test creating InspectieRonde model with sample data."""
    test_date = date(2025, 9, 25)

    record = InspectieRonde(
        locatie_samenvatting="1: 2x 1-2",
        baan_samenvatting="001",
        code="27014",
        klant_code="PT",
        bollen_code="ab41559-9-4",
        product_naam="T. Rocket 13",
        product_groep_naam="13 aziaat",
        datum_afleveren_plan=test_date,
        afwijking_afleveren=5,
        aantal_in_kas=398,
        aantal_tafels=2,
        productgroep_code=113,
        min_baan=1,
    )

    assert record.code == "27014"
    assert record.product_naam == "T. Rocket 13"
    assert record.afwijking_afleveren == 5
    assert record.datum_afleveren_plan == test_date
