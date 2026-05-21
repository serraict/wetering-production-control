---
name: dremio-sqlmodel
description: Inspect the project's Dremio instance and generate a SQLModel class + DremioRepository that match the existing patterns under src/production_control. Use this skill whenever the user wants to add, model, or expose a Dremio table/view in the app — e.g. "add a model for the spacing view", "create a repository for X", "what columns does Y have in Dremio", "discover tables in the Verkoop space", "wire up a new Dremio source", or any request that involves new data coming from Dremio. Use it even when the user does not explicitly say "SQLModel" or "repository"; modeling a Dremio source is what this skill is for.
---

# Dremio → SQLModel + Repository

This skill turns a Dremio table or view into a working `SQLModel` class and a `DremioRepository[T]` subclass that drops into `src/production_control/<domain>/`. It also covers how to inspect Dremio first when the user doesn't yet know what's there.

## When to apply

- The user names a Dremio source they want in the app ("model the `Verkoop.inspectie_ronde` view").
- The user wants to discover what's available ("what tables are in `Productie.Oppotten`?").
- The user asks to add a new repository, list page, or detail page for data that lives in Dremio — modeling is step one.
- The user is debugging a column mismatch between their model and the actual view.

If the source isn't in Dremio (Firebird, local SQLite, etc.), this skill does not apply.

## What you already have

The repo ships a CLI for ad-hoc Dremio queries:

```bash
uv run python scripts/dremio_cli/dremio_query.py "SELECT 1"
```

It reads `SIMPLE_QUERY_CONNECTION` (already set in the user's shell). Run this once at the start of a session to confirm connectivity before doing any modeling work — if it fails, the rest of the skill won't work and the user needs to fix their env first.

The base repository — `src/production_control/data/repository.py` — gives you `DremioRepository[T]` with pagination, text filtering, sorting, and the right workarounds for Dremio Flight's quirks (no real parameter binding, `bindparam(..., literal_execute=True)` for limits). Subclasses only fill in the model-specific pieces.

## Workflow

### 1. Verify the connection

```bash
uv run python scripts/dremio_cli/dremio_query.py "SELECT 1 AS ok"
```

If this returns a row, you're good. If not, stop and surface the error — don't try to model anything yet.

### 2. Discover what's there (only if needed)

Skip this when the user names a specific table. Otherwise, query `INFORMATION_SCHEMA`:

```sql
-- List schemas
SELECT DISTINCT TABLE_SCHEMA FROM INFORMATION_SCHEMA."TABLES" ORDER BY TABLE_SCHEMA;

-- List tables/views in a schema
SELECT TABLE_NAME, TABLE_TYPE
FROM INFORMATION_SCHEMA."TABLES"
WHERE TABLE_SCHEMA = 'Verkoop'
ORDER BY TABLE_NAME;
```

Note `INFORMATION_SCHEMA."TABLES"` needs the double quotes — `TABLES` is reserved.

### 3. Inspect the target table

Two passes — schema and data:

```sql
-- Column names + types
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'Verkoop' AND TABLE_NAME = 'inspectie_ronde'
ORDER BY ORDINAL_POSITION;
```

```sql
-- A few real rows to understand the data and confirm types
SELECT * FROM Verkoop.inspectie_ronde LIMIT 5;
```

The sample rows matter — `INFORMATION_SCHEMA` will tell you a column is `VARCHAR` but the data often reveals it's actually a date string, a code with leading zeros, or a numeric value stored as text. Pick Python types based on what the data looks like, not just the declared SQL type.

### 4. Pick a domain and file paths

Each Dremio source lives in its own domain folder under `src/production_control/<domain>/`. Existing examples: `potting_lots/`, `inspectie/`, `spacing/`, `bulb_picklist/`, `products/`. Reuse a folder if the new source belongs to an existing domain (e.g. another view in the inspection workflow). Otherwise create a new folder with `__init__.py`, `models.py`, `repositories.py`.

Use snake_case Python names. Field names mirror the database (often Dutch); titles and descriptions are Dutch too — match the style of the source you're modeling. Don't Anglicize names just because you can.

### 5. Write the model

Template (see `references/templates.md` for full examples and field-option details):

```python
"""<Domain> data models."""

from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel


class <ModelName>(SQLModel, table=True):
    """Model representing a <thing> record from <table_name>."""

    __tablename__ = "<table_name>"
    __table_args__ = {"schema": "<Schema.SubSchema>"}

    <primary_key>: <type> = Field(
        primary_key=True,
        title="<Dutch label>",
        description="<Dutch description>",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    <field>: Optional[<type>] = Field(
        default=None,
        title="<Dutch label>",
        description="<Dutch description>",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )
```

Type mapping (Dremio → Python):

| Dremio                | Python annotation     | Notes |
|-----------------------|-----------------------|-------|
| `INTEGER`, `BIGINT`   | `int`                 | |
| `DOUBLE`, `FLOAT`     | `float`               | |
| `DECIMAL(p,s)`        | `Decimal`             | `from decimal import Decimal` |
| `VARCHAR`, `CHAR`     | `str`                 | Check the data — codes with leading zeros stay strings. |
| `DATE`                | `date`                | `from datetime import date` |
| `TIMESTAMP`           | `datetime`            | `from datetime import datetime` |
| `BOOLEAN`             | `bool`                | |

Nullable columns get `Optional[T]` and `default=None`. The primary key never gets `Optional`. The `sa_column_kwargs={"info": {...}}` block carries UI hints used by the project's table renderer — `ui_sortable: True` for anything sortable, `ui_hidden: True` for fields shown only in the detail view, not the list. When in doubt, mark identifying/most-recent-action fields as visible and bulk metadata as hidden.

### 6. Write the repository

Template:

```python
"""<Domain> repositories."""

from typing import List, Optional, Tuple, Union

from sqlalchemy import Engine, Select, func, text
from sqlmodel import Session, select

from ..data import Pagination
from ..data.repository import DremioRepository
from .models import <ModelName>


class <ModelName>Repository(DremioRepository[<ModelName>]):
    """Repository for <thing> records."""

    search_fields = ["<col1>", "<col2>"]  # columns the filter box searches

    def __init__(self, connection: Optional[Union[str, Engine]] = None):
        super().__init__(<ModelName>, connection)

    def _apply_default_sorting(self, query: Select) -> Select:
        return query.order_by(self.model.<col>.desc(), self.model.<pk>)

    def get_paginated(
        self,
        page: int = 1,
        items_per_page: int = 10,
        sort_by: Optional[str] = None,
        descending: bool = False,
        filter_text: Optional[str] = None,
        pagination: Optional[Pagination] = None,
    ) -> Tuple[List[<ModelName>], int]:
        page, items_per_page, sort_by, descending = self._validate_pagination(
            page, items_per_page, sort_by, descending, pagination
        )
        with Session(self.engine) as session:
            base_query = select(<ModelName>)
            count_stmt = select(func.count(<ModelName>.<pk>))
            return self._execute_paginated_query(
                session, base_query, count_stmt,
                page, items_per_page, filter_text, self.search_fields,
                sort_by, descending,
            )

    def get_by_id(self, <pk>: <pk_type>) -> Optional[<ModelName>]:
        with Session(self.engine) as session:
            # text() because Dremio Flight doesn't support parameterized queries
            return session.exec(
                select(<ModelName>).where(text(f"<pk> = {<pk>!r}"))
            ).first()
```

A few patterns worth knowing — they exist because Dremio Flight is a less complete SQL surface than a normal database:

- **`text(f"... = ...")` for equality lookups.** The Flight protocol doesn't bind parameters, so you have to interpolate. Use `!r` for strings (gives you proper quoting) and plain `{}` for ints. *Only* do this with values you control — primary keys from URL routes are fine, free-form user input is not.
- **`bindparam(..., literal_execute=True)` for limits and offsets.** This *does* work for `LIMIT`/`OFFSET` and the base repository already uses it. Don't try `?` placeholders.
- **`_apply_text_filter` already exists** on the base class. The search box uses `lower(col) LIKE lower('%text%')` interpolation. List the columns in `search_fields` and you're done.
- **Pick the right primary key for `count(...)`.** Use the actual primary-key column, not `*`, so the count is cheap and unambiguous.

### 7. Validate with a query

Before declaring victory, run one real query through the new model. The fastest check:

```bash
uv run python -c "
from production_control.<domain>.repositories import <ModelName>Repository
r = <ModelName>Repository()
rows, total = r.get_paginated(items_per_page=3)
for row in rows: print(row)
print(f'total={total}')
"
```

If you get back rows whose fields populate sensibly, the model lines up with the view. If columns come back `None` that shouldn't be, the field name doesn't match the column name — check capitalization and underscores.

### 8. Tell the user what you did

Show the file paths created/edited, the table they map to, and any judgment calls — fields you marked `ui_hidden`, the default sort you picked, columns you guessed were nullable. The user can correct the small stuff faster than they can rederive it.

## What not to do

- Don't add fields the source view doesn't have, even "for completeness." If the user needs a derived field, ask first — it usually belongs in a Dremio view, not the model.
- Don't introduce SQLAlchemy parameter binding (`:name`, `?`) for `WHERE` clauses. Flight will reject it. The base class already handles the cases where it *does* work.
- Don't change `DremioRepository` itself to fit one source. Override on the subclass.
- Don't write tests for the new model unless the user asks — vibe-iterate first, codify what survives.
- Don't run `pip install` or edit `pyproject.toml` for ad-hoc query work — the existing `dremio_query.py` covers it via `uv`.

## References

- `references/templates.md` — full annotated examples of a model and repository, copied from `potting_lots` and `inspectie`, with comments on every field option.
- `references/dremio-quirks.md` — collected gotchas from working with Dremio Flight (parameter binding, reserved words, schema quoting).
