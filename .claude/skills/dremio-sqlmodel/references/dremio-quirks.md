# Dremio Flight quirks

Things that are easy to get wrong if you assume Dremio behaves like Postgres. Skim before debugging "this query works in DBeaver but not from the app."

## No parameter binding for WHERE clauses

The Arrow Flight transport doesn't bind parameters in `WHERE` predicates. SQLAlchemy will let you write `where(Model.id == :id)` and it'll fail at runtime against Dremio.

Use `text(f"...")` with interpolation:

```python
session.exec(select(M).where(text(f"id = {id}"))).first()              # int PK
session.exec(select(M).where(text(f"code = '{code}'"))).first()        # str PK — quote it
session.exec(select(M).where(text(f"code = {code!r}"))).first()        # equivalent, safer with odd chars
```

Only do this with values you control (URL path params, internal IDs). Free-form user input goes through `_apply_text_filter` on the base repository, which already does the right escaping for the `LIKE` use case.

## Parameter binding DOES work for LIMIT/OFFSET

Counter-intuitive but true — `LIMIT ? OFFSET ?` works via `bindparam(..., literal_execute=True)`. The base repository already uses this; copy the pattern if you need a custom paged query.

```python
query.limit(bindparam("limit", type_=Integer, literal_execute=True))
session.exec(query, params={"limit": 50})
```

`literal_execute=True` is the part that matters — without it SQLAlchemy will try to send the parameter through the (broken) bind mechanism.

## Reserved words need quoting

`INFORMATION_SCHEMA."TABLES"` — `TABLES` is reserved. Same with `COLUMNS` in some places, though it usually works unquoted. When in doubt, quote with double quotes.

```sql
SELECT * FROM INFORMATION_SCHEMA."TABLES" WHERE TABLE_SCHEMA = 'Verkoop';
```

## Schemas with dots

`Productie.Oppotten` is a single nested schema, not two. In `__table_args__` it's one string:

```python
__table_args__ = {"schema": "Productie.Oppotten"}
```

And in raw SQL the unquoted form usually just works:

```sql
SELECT * FROM Productie.Oppotten.oppotlijst LIMIT 1;
```

If a schema/table name has spaces or unusual characters, quote each segment with double quotes.

## Date/timestamp string formats

Dremio accepts ISO-formatted date/timestamp literals in `text()`-interpolated WHERE clauses:

```python
text(f"datum_afleveren_plan >= '{date_from}'")  # date_from is a datetime.date
```

`str(date(2026, 5, 20))` produces `'2026-05-20'` which Dremio happily parses. For timestamps, use `.isoformat()`.

## INFORMATION_SCHEMA is your friend for discovery

```sql
SELECT DISTINCT TABLE_SCHEMA FROM INFORMATION_SCHEMA."TABLES";
SELECT TABLE_NAME, TABLE_TYPE FROM INFORMATION_SCHEMA."TABLES" WHERE TABLE_SCHEMA = 'X';
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
  FROM INFORMATION_SCHEMA.COLUMNS
 WHERE TABLE_SCHEMA = 'X' AND TABLE_NAME = 'Y'
 ORDER BY ORDINAL_POSITION;
```

`TABLE_TYPE` distinguishes `TABLE` (PDS) from `VIEW` (VDS) — useful when the user asks "is this a Dremio view or a real table?"

## Types you'll see in the wild

- Dremio happily returns `VARCHAR` for things that are really codes, dates-as-text, or numbers-as-text. **Sample a few rows** before locking in a Python type — `SELECT … LIMIT 5` is part of the workflow, not optional.
- `DECIMAL(p,s)` should map to `decimal.Decimal`, not `float`. The project already has examples (`PottingLot.aantal_containers_oppotten`).
- Nullability from `INFORMATION_SCHEMA` is usually accurate for tables but pessimistic for views — when in doubt, treat view columns as `Optional`.
