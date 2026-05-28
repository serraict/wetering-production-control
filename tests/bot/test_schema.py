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
    assert "SELECT *" in out
