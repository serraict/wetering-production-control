# Doing

**Status: planned, not started.**

Slice A of the inspectieronde-changes fix. Triggered by Bianca's
report (2026-08-10): after a round in the greenhouse she gets no
overview list, and "Alles opslaan" sits below the partij rows instead
of in the dialog she saw on Thursday.

## Context

The inspectieronde page keeps a list of pending afwijking/afleverdatum
changes so Bianca can walk a round, tap +1/-1 per partij, and save the
whole list in one go at the end. She confirmed on 2026-08-10 that this
is what she wants — save-per-tap is *not* preferred, because the list
is also her check before committing.

Diagnosis of the 2026-08-10 report (no code changed since 2026-07-07,
only the size of her list did):

1. **The dialog has no height cap.** `ui.card().classes("w-full
   max-w-4xl")` (`inspectie.py:198`) wraps a plain `ui.table`
   (`inspectie.py:251`) with no `virtual-scroll` and no height, so the
   card grows to full row height. Quasar scrolls the whole card, not
   the table body. At 8 changes it fits (her Thursday photo — and even
   there the action buttons are already below the fold). At ~30
   changes the top of the list scrolls off screen and "Alles opslaan"
   ends up far below the rows. This is the reported symptom.

2. **A new `ui.dialog()` is built on every click and never removed.**
   NiceGUI's own `Dialog` docstring: "it is not removed when closed,
   but only hidden. You should either create it only once and then
   reuse it, or remove it with `.clear()` after dismissal."
   `handle_event` (`events.py:429-435`) parents each one to the sender's
   parent slot, so they pile up under the header button row, one per
   click, for the lifetime of the page. Same pattern at `scan.py:103`
   and `model_detail_page.py:100`. Best code-level match for "zoveel
   keer staat er dan eronder een blokje met opslaan", though not proven
   to be what renders inline.

3. **The list is not in the browser, despite the docstrings.**
   `get_storage()` (`inspectie.py:27-33`) returns `app.storage.user`,
   which NiceGUI stores server-side in
   `/app/.nicegui/storage-user-<session-id>.json`, keyed by the session
   cookie (`storage.py:102-118`). Every +1/-1 is a websocket
   round-trip, so a tap made while disconnected is silently lost —
   including the toast, which is server-side.

Session identity across a reconnect was checked and is **not** the
problem: the socket and the NiceGUI `Client` die (client deleted 3 s
after the drop, `client.py:272-284`, then a full page reload), but the
session cookie (`max_age` 14 days, `path=/`) and therefore
`_users[session_id]` survive, and nested writes do reach
`FilePersistentDict.backup()` via `ObservableCollection._observe`.
What does destroy the list is a **container recreate**: `_users` is
in-memory backed by `/app/.nicegui/`, and `docker-compose.yml` gives
`production_control` no volume.

## Goals

1. The pending-changes dialog stays usable at any list length — the
   list is visible and "Alles opslaan" is reachable without hunting
   below the rows.
2. Opening the dialog N times leaves N-1 fewer orphan elements in the
   page than it does today.
3. A redeploy of the `production_control` container no longer silently
   discards everyone's pending list.
4. A short connection dropout does not force a full page reload.

Explicitly *not* a goal here: making taps work while offline. See
"Follow-up slice" below.

## Acceptance criteria

- [ ] With 30+ pending changes on a phone-sized viewport, the dialog
      fits the screen: the table scrolls inside a capped-height card,
      and the "Alles wissen" / "Alles opslaan" row is visible without
      scrolling the card.
- [ ] Clicking the changes button 5 times creates exactly one dialog
      element; the pending-changes dialog is built once per page and
      its content refreshed on reopen.
- [ ] Reopening the dialog after a +1 shows the updated list (no stale
      content from the previous open).
- [ ] `docker compose down && up` on `production_control` preserves a
      pending list across the restart.
- [ ] `reconnect_timeout` is raised in `ui.run()`; a dropout shorter
      than the new timeout resumes without a page reload, verified in
      the browser by killing the network briefly.
- [ ] The `f"{n} afgevinkte partijten)"` typo at `inspectie.py:259` is
      fixed (stray paren + "partijten" → "partijen").
- [ ] `make quality` is green.
- [ ] (Manual, Bianca) A full round produces a readable list with a
      reachable save button.

## Design

- **Dialog height.** Card becomes a flex column with
  `max-h-[80vh]`; the `ui.table` goes in a `flex-1 overflow-auto`
  wrapper; the action row is a non-shrinking footer. Keep
  `print-preserve-columns` on the table so the print CSS at
  `styles.py:123-134` still applies.

- **Dialog lifecycle.** Build the dialog once in `inspectie_page()`
  and drive its body with a `@ui.refreshable` that reads storage on
  each open. `show_pending_changes_dialog` stops constructing UI and
  becomes "refresh + open". This also removes the `changes_state`
  plumbing currently threaded through every button handler for the
  dialog's sake — check what still needs it (the header badge does).

- **Storage volume.** Named volume mounted at `/app/.nicegui` for the
  `production_control` service. `Storage.path` honours
  `NICEGUI_STORAGE_PATH`, so an explicit env var is an option if a
  path outside the workdir is cleaner. Note in `docs/deployment.md`
  that this volume holds pending inspectie changes and must not be
  pruned casually.

- **Reconnect timeout.** `ui.run(..., reconnect_timeout=30)`. Knock-on
  effects, from `nicegui.py:125-126` and `outbox.py:118-124`:
  `ping_interval` becomes 24 s, `ping_timeout` 12 s, and the outbox
  message history window grows from ~9 s to ~66 s. Cost: the server
  takes up to ~36 s to notice a genuinely dead client and holds its
  element tree until then. Fine at this user count. Raise
  `message_history_length` only if the 1000 default proves tight —
  measure rather than guess.

- **What stays out of scope.** Migrating the pending changes to real
  browser storage; any offline queue; touching the `scan.py:103` and
  `model_detail_page.py:100` dialog leaks (same bug, different pages —
  fold in only if it is genuinely a one-liner each).

## Implementation steps

- [ ] Reproduce first: dev server, seed 30+ pending changes, confirm
      the dialog overflows on a phone-sized viewport. If it does not
      reproduce, stop and re-diagnose before changing anything.
- [ ] Restructure the dialog card (height cap, scrolling table body,
      pinned action row). Verify at 1, 8 and 30 changes.
- [ ] Move dialog construction to page build; make the body
      refreshable; simplify `show_pending_changes_dialog` to
      refresh + open. Update `tests/web/` accordingly.
- [ ] Fix the `partijten)` typo.
- [ ] Add the `.nicegui` volume to `docker-compose.yml`; document it
      in `docs/deployment.md`.
- [ ] Set `reconnect_timeout=30` in `__web__.py`; verify a short
      dropout resumes without reload.
- [ ] `make quality` green; commit.
- [ ] Write `work/notes/inspectie/pending_changes_v1_capture.md` with
      what reproduced, what did not, and what slice B still needs.

## Follow-up slice (needs a backlog line)

Move the pending changes into real browser storage (localStorage) so a
round genuinely survives being offline, with "Alles opslaan" flushing
when the connection is back. This is the only fix for "taps made while
disconnected are lost" — slice A does not address it. Open design
questions: keying, merge on reconnect, and what to show when a flush
partially fails.
