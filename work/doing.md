# Doing

## Context

Mistral smoke-run with two questions about "week 17" returned
`rows: 0` from Dremio because the model:

1. Compared the **string** column `oppot_week` against an ISO week
   label (`'2026-W17'`) — that column doesn't hold ISO labels.
2. Picked the wrong overview on retry (`registratie_controle` instead
   of `oppotlijst`).

Claude doesn't make those mistakes on the same prompt, but the prompt
also gives the model nothing to imitate: no example queries per
overview, and the only date-related guidance is the ISO 8601 display
rule — easy to misread as a filtering rule.

Two cheap system-prompt fixes that should help weaker models without
hurting stronger ones.

## Goals

1. The bot prefers filtering on date columns with a `BETWEEN` range
   over string-matching `*_week` columns.
2. Each overview ships an example query the model can pattern-match
   on (uses the right table, the right date column, a `BETWEEN`
   range).

## Acceptance criteria

- [ ] `SYSTEM_RULES` includes a "filter by date column, not by week
      string column" rule. Unit-tested.
- [ ] Each of the six overviews emits at least one example query that
      shows the canonical date column (where one exists). The
      examples are stable across runs.
- [ ] Examples use a clearly-non-current sample date range (so the
      model copies the shape, not the values).
- [ ] `make quality` is green.

## Design

- **System rule.** Add to `SYSTEM_RULES`: "For week-based filtering,
  use the date column (e.g. `oppot_datum`) with a `BETWEEN` range —
  do not string-match a `*_week` column against ISO week labels. The
  current week's bounds are in the Current date section above."
- **Schema examples.** Replace the single generic
  `Example: SELECT * FROM ... LIMIT 10` with a small per-overview
  dispatch in `schema.py`. Curated dict keyed by model class →
  example query string. Canonical date columns:
  - `PottingLot` → `oppot_datum`
  - `BulbPickList` → `oppot_datum`
  - `InspectieRonde` → `datum_afleveren_plan`
  - `Vloerplan19cm` → `datum_oppot_plan`
  - `WijderzetRegistratie` → `datum_oppotten_real`
  - `Product` → no date filter; example just shows a name search.
- **Sample dates.** Use `DATE '2024-01-01'` and `DATE '2024-01-07'`
  (Monday-Sunday of W01 2024) as the canonical range. Far enough in
  the past to obviously be example data; still ISO-week-aligned to
  reinforce the shape.
- **Determinism.** Same schemas + same example dict → same rendered
  string. No `now`-driven substitution in examples.
- **Tests.** Extend `test_schema.py`: assert each overview's example
  references its canonical date column (where defined) and the
  example range. Extend `test_answer.py`: assert the system prompt
  contains the new "filter by date column" rule.

## Implementation steps

- [ ] Add the date-column rule to `SYSTEM_RULES` in `bot/answer.py`.
- [ ] In `bot/schema.py`, add an `_EXAMPLES` dict keyed by model class
      → example SQL string and update `_render_overview` to use it
      with a fallback to the current generic example for models not
      listed.
- [ ] Update / extend `tests/bot/test_schema.py` to cover the new
      examples (per-overview canonical date column reference, stable
      output, sample date range).
- [ ] Add an assertion in `tests/bot/test_answer.py` that
      `SYSTEM_RULES` includes "do not string-match" (or the canonical
      phrasing).
- [ ] `make quality` green.
- [ ] (Manual) re-run the Mistral "week 17" smoke prompt and confirm
      Dremio now sees a date-range query.
