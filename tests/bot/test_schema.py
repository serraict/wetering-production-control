"""Tests for the SQLModel-based schema renderer."""

from __future__ import annotations

from production_control.bot import schema


def test_render_contains_all_overviews():
    out = schema.render()
    for model in schema.OVERVIEWS:
        assert model.__name__ in out, f"missing {model.__name__} in rendered schema"


def test_render_is_deterministic():
    assert schema.render() == schema.render()


def test_render_includes_qualified_view_names():
    out = schema.render()
    # Spot-check a known overview against its known Dremio location.
    assert '"Productie.Oppotten"."oppotlijst"' in out
    assert '"Verkoop"."inspectie_ronde"' in out


def test_render_lists_column_for_each_field():
    out = schema.render()
    # PottingLot has these columns in models.py; if the model is reshaped
    # the test will surface the drift.
    for column in ("id", "naam", "bollen_code", "oppot_datum"):
        assert f"`{column}`" in out


def test_render_uses_field_titles_when_present():
    out = schema.render()
    # `naam` has title="Artikel" in PottingLot.
    assert "Artikel" in out


def test_render_includes_example_query():
    out = schema.render()
    assert "Example:" in out
    assert "SELECT" in out


def test_each_overview_has_a_curated_example():
    """All overviews listed in OVERVIEWS must have an EXAMPLES entry."""
    for model in schema.OVERVIEWS:
        assert model in schema.EXAMPLES, f"no example query for {model.__name__}"


def test_examples_filter_on_canonical_date_columns():
    """Examples for date-bearing overviews reference the canonical date column."""
    expected = {
        schema.PottingLot: '"oppot_datum"',
        schema.BulbPickList: '"oppot_datum"',
        schema.InspectieRonde: '"datum_afleveren_plan"',
        schema.Vloerplan19cm: '"datum_oppot_plan"',
        schema.WijderzetRegistratie: '"datum_oppotten_real"',
    }
    for model, column in expected.items():
        assert column in schema.EXAMPLES[model], f"{model.__name__} example must reference {column}"


def test_examples_use_between_date_range_pattern():
    """Date-bearing examples use BETWEEN DATE ... AND DATE ...; they don't
    string-match a *_week column."""
    for model, sql in schema.EXAMPLES.items():
        if model is schema.Product:
            continue  # no date column; uses LIKE instead
        assert "BETWEEN DATE" in sql, f"{model.__name__} example should use BETWEEN DATE"
        assert "_week" not in sql, f"{model.__name__} example must not string-match a *_week column"


def test_examples_use_sample_w01_2024_range():
    """Sample range is intentionally non-current so the model copies the shape."""
    for model, sql in schema.EXAMPLES.items():
        if model is schema.Product:
            continue
        assert "'2024-01-01'" in sql
        assert "'2024-01-07'" in sql
