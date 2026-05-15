# Doing

## Context

- Operator scans a batch label and lands on `/scan/view/{id}` (`scan.py:86`),
  which renders a `PottingLot` (from oppotlijst).
- The afleverdatum (`datum_afleveren_plan`) lives on `InspectieRonde` (from
  `inspectie_ronde`), not on `PottingLot`. The inspectieronde page already
  supports `+1` / `-1` adjustments and a commit flow (`inspectie.py:331`,
  storage key `inspectie_changes` keyed by `InspectieRonde.code`).
- `PottingLot.id` (int) and `InspectieRonde.code` (str) are the same key
  under different names — convert with `str(lot.id)` (verify against a
  sample row during step 1).
- Operator wants to adjust afleverdatum from the scan view with the same
  storage + commit pipeline so both screens stay in sync.

## Goals

Single-click `+1` / `-1` adjustment of the afleverdatum on the scan view,
sharing storage and commit path with `/inspectie`.

## Acceptance criteria

- [ ] After scanning, one click changes afleverdatum by ±1 day.
- [ ] Pending change is stored in `app.storage.user["inspectie_changes"]`
      under the same `code` the inspectieronde page uses, so both screens
      see the same pending state and commit through the same endpoint.
- [ ] If the scanned lot has no matching InspectieRonde row, the afleverdatum
      card is not rendered.
- [ ] Scan view shows current effective afleverdatum: pending value if any,
      else the stored `datum_afleveren_plan`.
- [ ] A pending-changes count badge sits inline next to the ± / view
      buttons, linking to `/inspectie` (no commit dialog on scan view).
- [ ] Existing inspectieronde flow (table + card view, "Openstaande
      wijzigingen" dialog, commit) is unchanged.

## Design

### Data flow

```text
scan barcode → lot_id (int)
            → PottingLot
            → InspectieRepository.get_by_id(str(lot_id))
            → if found: render afleverdatum + ± buttons + pending badge
            → if missing: skip afleverdatum card
button click → shared delta handler
            → writes to storage["inspectie_changes"][code]
commit (from /inspectie page) → POST /api/firebird/update-afwijking
```

### Mapping PottingLot → InspectieRonde

`InspectieRonde.code == str(PottingLot.id)`. Implementation uses the
existing `InspectieRepository.get_by_id(code)` (`repositories.py:109`); no
new repository method needed. Step 1 of implementation verifies this with
a real row before the rest of the work proceeds.

### UI

Placement is already marked in `scan.py:128`: the third column of the
existing Klantcode/Afleverdatum card. The grid becomes:

1. `Klantcode` — value (unchanged)
2. `Afleverdatum` — effective date; if a pending change exists, show
   `original → new` styling (mirroring inspectieronde card view at
   `inspectie.py:568`)
3. `Acties` — `−`, `+`, `view` icon buttons (dense flat, matching the
   inspectieronde card view buttons at `inspectie.py:588-617`)

Reuse the same delta handler as `inspectie.create_afwijking_actions` —
extract to a shared helper so both pages call into one function. The
handler updates both `new_afwijking` and `new_datum` by the same delta,
matching current behavior.

The `view` button opens the `InspectieRonde` detail dialog
(`create_model_view_action` from `model_detail_page`).

A small badge sits inline next to the `−` / `+` / `view` buttons in
column 3, showing the total pending-changes count
(`len(get_pending_commands())`) and linking to `/inspectie`. Hidden when
zero.

If no `InspectieRonde` matches, replace the whole third card with the
current layout unchanged but afleverdatum shows `-` and the action column
is omitted (or render nothing in column 3).

### Out of scope

- Setting an arbitrary date via picker (only ±1).
- Committing from the scan view (badge links to `/inspectie` instead).
- Multi-lot scanning UX changes.

## Implementation steps

1. **Verify mapping.** Pick a scannable lot, confirm
   `InspectieRepository.get_by_id(str(lot.id))` returns the expected row.
   If wrong, stop and reopen the mapping question.
2. **Extract shared delta handler.** Move the inner `handler` body from
   `inspectie.create_afwijking_actions` (`inspectie.py:334-395`) into a
   module-level function in `production_control/inspectie/changes.py`
   (or similar), taking `code`, `current_afwijking`, `current_datum`,
   `delta`, plus the storage accessor. Update the inspectie page to call
   it. Keep storage shape identical so existing data still loads.
3. **Add the afleverdatum card to `scan.py:view_batch`.** After loading
   the `PottingLot`, call `InspectieRepository.get_by_id(str(lot.id))`.
   If missing → skip. If present → render card with effective date and
   ± buttons wired to the shared handler.
4. **Add pending-changes badge.** Reuse `get_pending_commands()` from
   `inspectie.py`. Render as a small `ui.badge`/`ui.button` near the
   "View Details" row linking to `/inspectie`, bound to count.
5. **Tests.**
   - Unit: shared `apply_delta` (no UI).
   - Integration: scanning + clicking `+` writes the expected entry to
     storage, and the same entry surfaces on `/inspectie`.
   - Unit: scan view skips the card when no InspectieRonde exists.
6. **Manual check.** Scan in browser, click `+` twice, open `/inspectie`,
   confirm pending change appears with `+2` / `+2 days`; commit; confirm
   clearing on both screens.
