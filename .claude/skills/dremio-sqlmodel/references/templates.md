# Full templates

Two complete, working examples copied from the codebase. When SKILL.md tells you to write a model or repository, start from one of these and adapt — they show exactly which imports, decorators, and field options the project uses.

## Model example: PottingLot

This is what `src/production_control/potting_lots/models.py` actually looks like (abbreviated to a handful of representative fields).

```python
"""Potting lots data models."""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlmodel import Field, SQLModel


class PottingLot(SQLModel, table=True):
    """Model representing a potting lot record from oppotlijst table."""

    __tablename__ = "oppotlijst"
    __table_args__ = {"schema": "Productie.Oppotten"}

    # Primary key — never Optional
    id: int = Field(
        primary_key=True,
        title="ID",
        description="The potting lot identifier",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    # Required string column (NOT NULL in the source)
    naam: str = Field(
        title="Artikel",
        description="The plant variety name",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    # Nullable date — Optional + default=None
    oppot_datum: Optional[date] = Field(
        default=None,
        title="Oppot Datum",
        description="The planting date",
        sa_column_kwargs={"info": {"ui_sortable": True}},
    )

    # Nullable decimal — for counts/amounts where precision matters
    aantal_containers_oppotten: Optional[Decimal] = Field(
        default=None,
        title="Aantal Containers",
        description="Number of containers",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )

    # Hidden-by-default field — shown in detail view but not the table
    olsthoorn_bollen_code: Optional[str] = Field(
        default=None,
        title="Olsthoorn Bollen Code",
        description="Olsthoorn bulb code",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}},
    )
```

### Field-option cheat sheet

- `primary_key=True` — exactly one field. Don't make it `Optional`.
- `default=None` — required on every nullable column so SQLModel can construct rows from partial data.
- `title="…"` — the column header in the list view. Dutch, short, matches what the user calls the field on screen.
- `description="…"` — used as the tooltip / detail-view label. Dutch, a sentence-ish.
- `sa_column_kwargs={"info": {"ui_sortable": True}}` — almost always true; lets the table component sort by the column.
- `sa_column_kwargs={"info": {"ui_sortable": True, "ui_hidden": True}}` — column exists on the model and detail page, but is hidden from the list table. Use for metadata, internal codes, remarks.

A `__str__` is worth adding when the record has an obvious human label (see `InspectieRonde.__str__` for an example).

## Repository example: InspectieRepository

From `src/production_control/inspectie/repositories.py`. This one is richer than the minimum because it adds date filtering — useful as a reference when the user wants filters beyond plain text search.

```python
"""Inspectie repository for data access."""

from datetime import date, timedelta
from typing import List, Optional, Tuple, Union

from sqlalchemy import Engine, Select, func, text
from sqlmodel import Session, select

from ..data import Pagination
from ..data.repository import DremioRepository
from .models import InspectieRonde


class InspectieRepository(DremioRepository[InspectieRonde]):
    """Repository for accessing inspectieronde data from Dremio."""

    search_fields = ["code", "product_naam", "product_groep_naam", "klant_code"]

    def __init__(self, connection: Optional[Union[str, Engine]] = None):
        super().__init__(InspectieRonde, connection)

    def _apply_default_sorting(self, query: Select) -> Select:
        return query.order_by(
            self.model.min_baan,
            InspectieRonde.datum_afleveren_plan,
            self.model.product_naam,
            self.model.code,
        )

    def _apply_date_filter(
        self,
        query: Select,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        default_filter: Optional[str] = None,
    ) -> Select:
        if default_filter == "next_two_weeks":
            today = date.today()
            date_from = today - timedelta(days=7)
            date_to = today + timedelta(days=14)

        if date_from is not None:
            # text() — Dremio Flight doesn't bind parameters
            query = query.where(text(f"datum_afleveren_plan >= '{date_from}'"))
        if date_to is not None:
            query = query.where(text(f"datum_afleveren_plan <= '{date_to}'"))
        return query

    def get_paginated(
        self,
        page: int = 1,
        items_per_page: int = 10,
        sort_by: Optional[str] = None,
        descending: bool = False,
        filter_text: Optional[str] = None,
        pagination: Optional[Pagination] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        default_filter: Optional[str] = None,
    ) -> Tuple[List[InspectieRonde], int]:
        page, items_per_page, sort_by, descending = self._validate_pagination(
            page, items_per_page, sort_by, descending, pagination
        )
        with Session(self.engine) as session:
            base_query = select(InspectieRonde)
            count_stmt = select(func.count(InspectieRonde.code))

            base_query = self._apply_date_filter(base_query, date_from, date_to, default_filter)
            count_stmt = self._apply_date_filter(count_stmt, date_from, date_to, default_filter)

            return self._execute_paginated_query(
                session, base_query, count_stmt,
                page, items_per_page, filter_text, self.search_fields,
                sort_by, descending,
            )

    def get_by_id(self, code: str) -> Optional[InspectieRonde]:
        with Session(self.engine) as session:
            return session.exec(
                select(InspectieRonde).where(text(f"code = '{code}'"))
            ).first()
```

### Notes

- `search_fields` lists columns the free-text search box hits. Pick fields a user would naturally type — codes, names, customer references. Don't include long descriptive text.
- `_apply_default_sorting` is the answer to "what order should rows be in when no sort is selected?" Often newest-first by date plus the primary key for stability.
- `get_by_id` parameter name and type match the primary key on the model — `id: int` for `PottingLot`, `code: str` for `InspectieRonde`.
- When the count needs to be cheap and unambiguous, use `func.count(<pk>)` rather than `func.count()` or `*`.
- The simpler `PottingLotRepository` (no date filter) is a good starting point if the new source doesn't need extra filtering — drop the `_apply_date_filter` and the extra kwargs.
