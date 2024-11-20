"""Tests for CLI commands."""

from datetime import date
from uuid import uuid4
from pytest import MonkeyPatch
from typer.testing import CliRunner
from production_control.__cli__ import app
from production_control.products.models import Product
from production_control.spacing.models import WijderzetRegistratie

runner = CliRunner()


def test_version():
    """Test version command."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "version" in result.stdout


def test_products_command(monkeypatch: MonkeyPatch):
    """Test products list command."""

    class MockProductRepository:
        def get_all(self):
            return [
                Product(
                    id=1,
                    name="Test Product 1",
                    product_group_id=100,
                    product_group_name="Test Group A",
                ),
                Product(
                    id=2,
                    name="Test Product 2",
                    product_group_id=200,
                    product_group_name="Test Group B",
                ),
            ]

    monkeypatch.setattr(
        "production_control.__cli__.ProductRepository",
        lambda: MockProductRepository(),
    )

    result = runner.invoke(app, ["products"])
    assert result.exit_code == 0
    assert "Products" in result.stdout
    assert "Test Product 1" in result.stdout
    assert "Test Group A" in result.stdout
    assert "Test Product 2" in result.stdout
    assert "Test Group B" in result.stdout


def test_spacing_errors_command(monkeypatch: MonkeyPatch):
    """Test spacing errors list command."""

    class MockSpacingRepository:
        def get_error_records(self):
            return [
                WijderzetRegistratie(
                    id=uuid4(),
                    partij_code="TEST-001",
                    product_naam="Test Product",
                    productgroep_naam="Test Group",
                    aantal_planten_gerealiseerd=100,
                    aantal_tafels_totaal=10,
                    aantal_tafels_na_wdz1=15,
                    aantal_tafels_na_wdz2=20,
                    aantal_tafels_oppotten_plan=10,
                    dichtheid_oppotten_plan=100,
                    dichtheid_wz1_plan=50,
                    datum_oppotten_real=date(2024, 1, 1),
                    wijderzet_registratie_fout="Test error message",
                )
            ]

    monkeypatch.setattr(
        "production_control.__cli__.SpacingRepository",
        lambda: MockSpacingRepository(),
    )

    result = runner.invoke(app, ["spacing-errors"])
    assert result.exit_code == 0
    # Check table headers
    assert "Spacing Records with Errors" in result.stdout
    assert "Partij" in result.stdout
    assert "Product" in result.stdout
    assert "Productgroep" in result.stdout
    assert "Oppotdatum" in result.stdout
    assert "Fout" in result.stdout
    # Check record data
    assert "TEST-001" in result.stdout
    assert "Test Product" in result.stdout
    assert "Test Group" in result.stdout
    assert "2024-01-01" in result.stdout
    assert "Test error message" in result.stdout


def test_spacing_error_filter_command(monkeypatch: MonkeyPatch):
    """Test spacing error filter command."""

    class MockSpacingRepository:
        def get_error_records(self):
            return [
                WijderzetRegistratie(
                    id=uuid4(),
                    partij_code="TEST-001",
                    product_naam="Test Product 1",
                    productgroep_naam="Test Group",
                    aantal_planten_gerealiseerd=100,
                    aantal_tafels_totaal=10,
                    aantal_tafels_na_wdz1=15,
                    aantal_tafels_na_wdz2=20,
                    datum_oppotten_real=date(2024, 1, 1),
                    wijderzet_registratie_fout="Geen wdz2 datum maar wel tafel aantal na wdz 2",
                ),
                WijderzetRegistratie(
                    id=uuid4(),
                    partij_code="TEST-002",
                    product_naam="Test Product 2",
                    productgroep_naam="Test Group",
                    aantal_planten_gerealiseerd=100,
                    aantal_tafels_totaal=10,
                    aantal_tafels_na_wdz1=15,
                    aantal_tafels_na_wdz2=20,
                    datum_oppotten_real=date(2024, 1, 2),
                    wijderzet_registratie_fout="Partij is 2x wdz maar het tafelaantal is niet juis geregistreerd",
                ),
            ]

    monkeypatch.setattr(
        "production_control.__cli__.SpacingRepository",
        lambda: MockSpacingRepository(),
    )

    # Test filtering by "Geen wdz2 datum"
    result = runner.invoke(app, ["spacing-errors", "--error", "Geen wdz2 datum"])
    assert result.exit_code == 0
    assert "TEST-001" in result.stdout
    assert "Test Product 1" in result.stdout
    assert "2024-01-01" in result.stdout
    assert "TEST-002" not in result.stdout

    # Test filtering by "tafelaantal is niet juis"
    result = runner.invoke(app, ["spacing-errors", "--error", "tafelaantal is niet juis"])
    assert result.exit_code == 0
    assert "TEST-002" in result.stdout
    assert "Test Product 2" in result.stdout
    assert "2024-01-02" in result.stdout
    assert "TEST-001" not in result.stdout

    # Test no matches found
    result = runner.invoke(app, ["spacing-errors", "--error", "nonexistent error"])
    assert result.exit_code == 0
    assert "No records found with error matching: nonexistent error" in result.stdout
