"""Tests for potting lots models."""

from datetime import date
from decimal import Decimal
from production_control.potting_lots.models import PottingLot


def test_potting_lot_model_exists():
    """Test PottingLot model exists."""
    assert PottingLot is not None


def test_potting_lot_model_attributes():
    """Test PottingLot model has expected attributes."""
    # Arrange
    test_date = date(2023, 1, 1)  # January 1, 2023 (week 52)

    # Act
    potting_lot = PottingLot(
        id=1001,
        naam="Test Plant",
        bollen_code=12345,
        oppot_datum=test_date,
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
        product_groep="Test Product Group",
        klant_code="CUST123",
        oppot_week="2023-01",
    )

    # Assert
    assert potting_lot.id == 1001
    assert potting_lot.naam == "Test Plant"
    assert potting_lot.bollen_code == 12345
    assert potting_lot.oppot_datum == test_date
    assert potting_lot.productgroep_code == 42
    assert potting_lot.bolmaat == 16.5
    assert potting_lot.bol_per_pot == 3.0
    assert potting_lot.rij_cont == 4
    assert potting_lot.olsthoorn_bollen_code == "OBC123"
    assert potting_lot.aantal_pot == 100
    assert potting_lot.aantal_bol == 300
    assert potting_lot.aantal_containers_oppotten == Decimal("25.0")
    assert potting_lot.water == "Normal"
    assert potting_lot.fust == "Standard"
    assert potting_lot.opmerking == "Test remark"
    assert potting_lot.product_groep == "Test Product Group"
    assert potting_lot.klant_code == "CUST123"
    assert potting_lot.oppot_week == "2023-01"


def test_potting_lot_model_optional_fields():
    """Test PottingLot model with only required fields."""
    # Act
    potting_lot = PottingLot(
        id=1001,
        naam="Test Plant",
        bollen_code=12345,
    )

    # Assert
    assert potting_lot.id == 1001
    assert potting_lot.naam == "Test Plant"
    assert potting_lot.bollen_code == 12345
    assert potting_lot.oppot_datum is None
    assert potting_lot.productgroep_code is None
    assert potting_lot.bolmaat is None
    assert potting_lot.bol_per_pot is None
    assert potting_lot.rij_cont is None
    assert potting_lot.olsthoorn_bollen_code is None
    assert potting_lot.aantal_pot is None
    assert potting_lot.aantal_bol is None
    assert potting_lot.aantal_containers_oppotten is None
    assert potting_lot.water is None
    assert potting_lot.fust is None
    assert potting_lot.opmerking is None
    assert potting_lot.product_groep is None
    assert potting_lot.klant_code is None
    assert potting_lot.oppot_week is None
