# OS ↔ PC protocol v1 — capture

Findings from shipping v1 (Steps 1–7, since rolled out of
`work/doing.md`). Durable surprises that future work on the protocol
should be aware of.

## What surprised us

### Leuze publishes duplicate scans with fresh timestamps

asyncua's default `subscribe_data_change` uses `DataChangeTrigger.StatusValue`,
which suppresses notifications when the value (and status) match the
previous sample. The real Leuze re-emits the same URL when the same
barcode is scanned again — same `Value`, fresh `SourceTimestamp` — so the
default trigger silently dropped the second scan and the *duplicate-after-ack*
scenario hung.

Fix: build a `MonitoredItemCreateRequest` manually with
`DataChangeFilter.Trigger = StatusValueTimestamp` and call
`create_monitored_items` directly. See `_make_timestamp_trigger_request`
in `src/production_control/opcua/protocol/scan_cycle.py`. Worth confirming
the real Leuze actually publishes a fresh SourceTimestamp on each scan
when we next have one on a workbench.

### behave's step loader breaks relative imports

behave exec's step modules without `__name__`, so any `from ._helpers
import …` fails with `KeyError: '__name__' not in globals`. The
documented workarounds (using `environment.py` to install helpers, or
putting shared code in a sibling module) felt heavier than the problem.

Fix: inline the small asyncua read/write helpers into each step module
(`plc_steps.py`, `os_steps.py`). If the helpers grow, promote them to a
non-step module like `features/protocol/_helpers.py` imported via the
absolute path `production_control.opcua._test_helpers`, not via a
relative import.

### asyncio teardown spew unless the handler waits on a stop_event

First cut cancelled the gather task to stop the handler. asyncua's
`async with client:` never got to run, so each scenario teardown logged
a CancelledError stack. Fix: thread a `stop_event` through `run_protocol`
and the per-source loops, await it instead of relying on cancellation,
and the client disconnect runs cleanly.

### Test server needs forced namespace indexes

Production has Omron at `ns=4` and Leuze at `ns=5`. Naïvely registering
the namespaces in `scripts/opc_test_server.py` gave them `ns=2` / `ns=3`,
so the production node-id strings didn't resolve. Fix: register two
padding namespaces (`urn:opc-test:padding-2/3`) before the real ones so
the indexes line up with prod. See `PADDING_NAMESPACES` in the script.

### `uawrite` type names are lowercase

`-t String` errors out (`invalid choice 'String'`). Use `-t string`,
`-t int32`. Not in our code path, but came up while smoke-testing the
test server with `uawrite`.

## What's deferred to v3

- Edge-case scenarios: unparseable scan URLs, scan during OS startup,
  scan while PC is mid-write. Placeholder feature file:
  `features/protocol/edge_cases.feature`.
- Connection-recovery scenarios: PLC drops/recovers, Leuze drops/recovers,
  scans during outage dropped (not queued). Placeholder:
  `features/protocol/connection_recovery.feature`. Today the per-source
  `supervise()` in `src/production_control/opcua/monitor.py` handles
  this; v1 verifies it only by hand.
- Promoting `docs/protocol.md` from prose to a generated artifact of the
  Gherkin spec.

## Scope decisions worth remembering

- Dropped the `_node_ids[line]["os_active"]` and `last_updated` writes
  from `PottingLineController`. Neither was read by anything shipped,
  and keeping them in sync was protocol noise.
- Operator UI test calls `PottingLineController.set_active_lot` directly
  rather than driving NiceGUI. That keeps the executable spec focused on
  the OPC contract and out of UI-framework flakiness.

## Stats at v1 close

- behave: 2 features, 8 scenarios (4 `scan_cycle` + 4 `active_partij`).
- unit tests: 296 passing, 1 skipped, 10 deselected.
- New production modules: `src/production_control/opcua/protocol/{__init__,
  __main__, scan_parser, scan_cycle}.py`.
- Touched: `src/production_control/potting_lots/line_controller.py`,
  `scripts/opc_test_server.py`, Makefile, CI via `make quality`.
