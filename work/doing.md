# Doing

## Context

Several list pages render a row "view" button via
`create_model_view_action` in `web/components/model_detail_page.py` and
pass it through `row_actions={"view": ...}` to
`display_model_list_page`. `potting_lots.py` already extends the pattern
with a sibling `create_label_action` ("label"). A few list pages now
correspond to records that also have a scan-page route
(`potting_lots.py: @router.page("/scan/{id}")`,
`bulb_picklist.py: @router.page("/scan/{id}")`), and `inspectie.py`
already builds the same potting-lots scan URL by hand.

Right now, getting to a row's scan page from the list means navigating
away manually. We want it one click from the row.

## Goals

Per-row "scan" action shown next to the existing view button on every
list page whose rows correspond to a record with a scan page.

## Acceptance criteria

- [x] New `create_scan_action(...)` helper in
      `web/components/model_detail_page.py`, mirroring the shape of
      `create_model_view_action` (returns `{"icon", "handler"}`).
- [x] Wired into `row_actions` on potting_lots, inspectie,
      bulb_picklist, spacing, and uitrijden list pages — all five
      route through `potting_lot_scan` because every list's row is a
      potting lot under the hood.
- [x] Tests in `tests/web/test_scan_action.py` cover the helper
      contract + the route-name contract for both `potting_lot_scan`
      and `bulb_picklist_scan`.
- [x] `make quality` green.

## Design

- Helper signature draft:
  ```python
  def create_scan_action(scan_url_for: Callable[[Any], str]) -> dict:
      return {
          "icon": "qr_code_scanner",  # matches theme.py scanner button
          "handler": lambda e: ui.navigate.to(scan_url_for(e.args.get("key"))),
      }
  ```
- Callers build the URL using `router.url_path_for(...)` per
  [URL construction in web pages] memory — e.g.
  `create_scan_action(lambda id: router.url_path_for("potting_lot_scan", id=id))`.
  This intentionally diverges from `create_model_view_action`'s
  hardcoded `detail_url="{id}"` pattern; refactoring the older helper
  is out of scope here.
- Icon: `qr_code_scanner` (same as the global scanner button in
  `web/components/theme.py`) so the affordance reads consistently.
- For pages whose scan URL lives on a different router
  (inspectie → potting-lots scan), pass the right router into
  `url_path_for`. Confirm each route name during implementation.

## Implementation steps

- [x] Add `create_scan_action` to
      `web/components/model_detail_page.py` and a unit test for the
      handler (mock `ui.navigate.to`, assert it's called with the URL
      `scan_url_for` returned).
- [x] Wire `"scan": create_scan_action(...)` into `row_actions` on
      `potting_lots.py`, `inspectie.py`, `bulb_picklist.py`. Verify
      each route name with the actual `@router.page` decorator.
- [x] Audit `spacing.py` and `uitrijden.py`; add if applicable, note
      and skip if not.
- [x] Add focused web tests asserting the route names the scan
      actions depend on (`potting_lot_scan`, `bulb_picklist_scan`).
- [x] `make quality`.

## Capture

- Open question from the design ("does `e.args["key"]` give the
  right value for every list?") resolved cleanly:
  `display_model_list_page` always uses `row_key="id"` and
  `table_utils.format_row` always puts the model's PK value under the
  `"id"` key — regardless of whether the actual PK field is `id`
  (potting_lots, bulb_picklist) or `code` (inspectie). So the lambda
  only needs `e.args["key"]`, no special-case extractor.
- Inspectie reuses the potting-lots scan URL because its records have
  no scan route of their own. Importing `potting_lots.router` at
  module top would form a cycle (potting_lots → scan → inspectie), so
  the import is lazy inside `inspectie_page()`. Documented in-line.
- All five list pages (potting_lots, inspectie, bulb_picklist,
  spacing, uitrijden) route through `view_batch` on the scan router —
  every list's primary key is a potting-lot id under the hood.
  Confirmed mid-slice by the user. Saved a memory entry so future-me
  doesn't ask again.
- First wired to `potting_lot_scan` (the canonical
  `/potting-lots/scan/{id}` URL); user reported "back twice to get to
  the list" — that route is a server-side `ui.navigate.to(...)`
  redirect, so the intermediate URL ends up in browser history before
  the actual `view_batch` page does. Switched all five row actions to
  navigate directly to `view_batch`. The `potting_lot_scan` route
  stays for external barcode scans / the OPC protocol URL.
