"""Render the project's SQLModel overviews as system-prompt context.

Same source of truth as the app's list pages, so the bot can never
describe a column the app doesn't already know about.
"""

from __future__ import annotations

from typing import Type

from sqlmodel import SQLModel

from production_control.bulb_picklist.models import BulbPickList
from production_control.inspectie.models import InspectieRonde
from production_control.potting_lots.models import PottingLot
from production_control.products.models import Product
from production_control.spacing.models import WijderzetRegistratie
from production_control.vloerplan.models import Vloerplan19cm

# Order matters: keep prompts stable across runs.
OVERVIEWS: list[Type[SQLModel]] = [
    PottingLot,
    BulbPickList,
    InspectieRonde,
    Product,
    Vloerplan19cm,
    WijderzetRegistratie,
]

# Per-overview example queries. The sample date range (W01-2024,
# Mon 2024-01-01 to Sun 2024-01-07) is intentionally non-current so
# the model copies the shape, not the values; the current-week
# bounds are in the temporal context block. Each example references
# the canonical date column so the model doesn't try to string-match
# a `*_week` column against an ISO label.
EXAMPLES: dict[Type[SQLModel], str] = {
    PottingLot: (
        'SELECT "id", "naam", "aantal_pot" '
        'FROM "Productie.Oppotten"."oppotlijst" '
        "WHERE \"oppot_datum\" BETWEEN DATE '2024-01-01' AND DATE '2024-01-07' "
        'ORDER BY "aantal_pot" DESC LIMIT 10'
    ),
    BulbPickList: (
        'SELECT "id", "ras", "aantal_bollen" '
        'FROM "Productie.Oppotten"."bollen_pick_lijst" '
        "WHERE \"oppot_datum\" BETWEEN DATE '2024-01-01' AND DATE '2024-01-07' "
        'ORDER BY "aantal_bollen" DESC LIMIT 10'
    ),
    InspectieRonde: (
        'SELECT "code", "klant_code", "product_naam", "aantal_in_kas" '
        'FROM "Verkoop"."inspectie_ronde" '
        "WHERE \"datum_afleveren_plan\" BETWEEN DATE '2024-01-01' AND DATE '2024-01-07' "
        'ORDER BY "datum_afleveren_plan" LIMIT 10'
    ),
    Product: (
        'SELECT "id", "name", "product_group_name" '
        'FROM "Vines"."products" '
        "WHERE LOWER(\"name\") LIKE '%lily%' LIMIT 10"
    ),
    Vloerplan19cm: (
        'SELECT * FROM "Productie.Plan"."vloerplan_19cm" '
        "WHERE \"datum_oppot_plan\" BETWEEN DATE '2024-01-01' AND DATE '2024-01-07' "
        "LIMIT 10"
    ),
    WijderzetRegistratie: (
        'SELECT * FROM "Productie.Controle"."registratie_controle" '
        "WHERE \"datum_oppotten_real\" BETWEEN DATE '2024-01-01' AND DATE '2024-01-07' "
        "LIMIT 10"
    ),
}


def _full_table(model: Type[SQLModel]) -> str:
    """Return the fully-qualified Dremio view name in quoted form."""
    table_args = getattr(model, "__table_args__", None) or {}
    schema = table_args.get("schema") if isinstance(table_args, dict) else None
    if schema:
        return f'"{schema}"."{model.__tablename__}"'
    return f'"{model.__tablename__}"'


def _field_descriptions(model: Type[SQLModel]) -> dict[str, str]:
    """Pull title/description off the Pydantic FieldInfo for each column."""
    fields = getattr(model, "model_fields", None) or getattr(model, "__fields__", {})
    out: dict[str, str] = {}
    for name, fi in fields.items():
        title = getattr(fi, "title", None) or ""
        desc = getattr(fi, "description", None) or ""
        label = title or desc
        if label:
            out[name] = label
    return out


def _render_overview(model: Type[SQLModel]) -> str:
    table = _full_table(model)
    labels = _field_descriptions(model)

    lines = [
        f"### {model.__name__}",
        f"Dremio view: {table}",
        "",
        "Columns:",
    ]
    for col in model.__table__.columns:
        sql_type = col.type.__class__.__name__.upper()
        nullable = " NULL" if col.nullable else ""
        label = labels.get(col.name, "")
        suffix = f" — {label}" if label else ""
        lines.append(f"  - `{col.name}` {sql_type}{nullable}{suffix}")

    lines.append("")
    example = EXAMPLES.get(model, f"SELECT * FROM {table} LIMIT 10")
    lines.append(f"Example: `{example}`")
    return "\n".join(lines)


def render() -> str:
    """Render all overviews as a single markdown block."""
    parts = ["## Available overviews", ""]
    for model in OVERVIEWS:
        parts.append(_render_overview(model))
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"
