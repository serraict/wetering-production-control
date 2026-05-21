# Doing: PLC Monitor v3 — Textual TUI

Operator-facing live view of both sources. Smallest next slice of
[[plc_monitoring_app]] after v2.

Full note: [`work/notes/plc_monitoring_app.md`](notes/plc_monitoring_app.md).

## Context

v1+v2 ship a headless monitor that streams JSONL for both PLC and Leuze.
That's enough for diagnostics by tail+grep, but not great if an operator on
serraserver just wants to see "what's the line doing right now". A Textual
TUI over ssh fits that use case, and Textual is async-native so it shares the
existing asyncua event loop cleanly.

Per the slice plan: v3 TUI is standalone (no JSONL persisted while TUI runs);
v4 adds file logging; v5 picks a persistent runtime.

## Goals

1. `python -m production_control.opcua.tui` opens a Textual app that connects
   to PLC + Leuze using the same env vars as `monitor`, and shows live
   values for every monitored node.
2. Headless `python -m production_control.opcua.monitor` still works
   unchanged — the TUI is a peer entry point, not a mode flag.

## Acceptance criteria

- [ ] `python -m production_control.opcua.tui` runs over ssh (no mouse
      assumed) and renders two `DataTable`s — one per source — with rows
      updated live as datachange notifications arrive.
- [ ] Header for each source shows: connection status (connected /
      reconnecting / giving up), seconds since last update, attempt counter
      when not connected.
- [ ] PLC `DeviceStatus.Mode` and `DeviceStatus.ErrorStatus` are pulled
      into the source header (always visible), not just rows in the table.
- [ ] `q` quits.
- [ ] If the Leuze env vars are unset, only the PLC pane shows (matching
      monitor's "Leuze source skipped" behavior).
- [ ] Runs from the `opcua_test` container against the production PLC and
      shows live values; verified by user on serraserver.

## Design

- New module `production_control/opcua/tui.py`. A Textual `App` with two
  panes (PLC + Leuze), each a `Static` header + a `DataTable`.
- Refactor: extract a `StateHandler` (sibling of `JsonlHandler`) that, on
  each datachange, updates a shared `dict[(source, node_id), Record]` and
  emits a Textual message so the TUI can repaint. Or: simpler v3 — keep a
  shared dict + the TUI uses a `set_interval(0.25, repaint)` to poll. Start
  with polling, switch to push if it feels laggy.
- The asyncua `run_plc` / `run_leuze` coroutines already take *nothing* —
  they construct their own `JsonlHandler`. Refactor to accept a handler
  factory so TUI can pass in a `StateHandler` factory while monitor keeps
  its `JsonlHandler` factory.
- Reuse `supervise()` from monitor for the same reconnect/backoff behavior.
  Supervisor `name` (already a parameter) lets the TUI subscribe to status
  changes — quick & dirty: also write status into the shared state.
- Quit key handled by Textual's default footer / `BINDINGS = [("q",
  "quit", "Quit")]`.

### Layout sketch

```
┌─ Potting PLC (10.0.0.190) ──────────────────────────────────────────────┐
│ connected  ·  Mode: RUN  ·  ErrorStatus: ContinuousError  ·  upd 0.4s ago│
│ Node                                  Value                   Updated   │
│ AantalBollenPerKrat                   0                       2s ago    │
│ ActievePartijnummer1                  12345                   12s ago   │
│ ActievePartijnummer2                  0                       12s ago   │
│ ScanResultaat                         0                       12s ago   │
│ UnpublishedVariablesStatus            0                       42s ago   │
│ NumOfVars                             4                       42s ago   │
│ NumOfValues                           4                       42s ago   │
├─ Leuze (10.0.0.191) ────────────────────────────────────────────────────┤
│ reconnecting (attempt 4/10)  ·  next try in 32s                         │
│ LastScanData                          —                       —         │
│ ScanActive                            —                       —         │
│ DeviceTemperature                     —                       —         │
└──────────────────────────────────────────────────────────  q: quit  ────┘
```

### Explicitly out of scope for v3

- File logging — v4.
- Interactive features (sorting, filtering, copy-to-clipboard,
  drill-into-node history) — only if asked.
- Replay from a JSONL file — interesting but a separate tool.
- Triggering writes from the TUI.

## Implementation steps

- [x] Add `textual` as a runtime dep (`uv add textual` → textual 8.2.7).
- [x] Refactor `monitor.run_plc` / `leuze.run_leuze` to take a `handler`
      parameter. `monitor.main()` constructs `JsonlHandler`s and passes
      them via `functools.partial`; headless monitor behavior unchanged
      (verified via regression test).
- [x] `production_control/opcua/tui.py` with `StateHandler`, a Textual
      `App` rendering both panes, and a `cli()` entry point that wires
      both supervised tasks to feed the `StateHandler`s. Leuze pane is
      conditionally rendered when `VINEAPP_OPCUA_LEUZE_URL` is set.
- [x] Local sanity check via Textual's `App.run_test()` against
      `opc_test_server.py`: state populates with 5 vars within 2s, PLC
      table renders 5 rows, `uawrite` to a PLC var reflects in state
      within 1s, Leuze pane absent when env unset.
- [ ] Build + push image (`make docker_push`).
- [ ] On serraserver:
      `docker compose run --rm -it opcua_test python -m production_control.opcua.tui`
      against the production PLC. Confirm it renders and updates.
- [ ] Capture findings (anything ugly in the layout, lag, weird Textual
      quirks over ssh) in
      `work/notes/ontstapelmachine/plc_monitor_v3_capture.md` and fold
      back into the long-form note.
