# PLC Monitoring App

A read-only window on the OPC/UA values exposed by the Leuze scanner and the
Potting PLC. Operator-facing dashboard plus a structured logger for later
analysis. Separate from the OS↔PC protocol implementation
([[os_pc_protocol_implementation]]); they share the connection layer but no
state.

## Purpose

- Give an operator on `serraserver` a live view of "what is the line saying
  right now" over ssh, without needing the web app or UaExpert.
- Capture a continuous record of the protocol-relevant OPC values so we can
  diagnose incidents after the fact.

## Scope

### Monitored nodes (initial fixed set)

Protocol nodes plus a small curated extras list.

PLC (`opc.tcp://10.0.0.190:4840`, `ns=4;s=OPCScanner/fbOPC/...`):

- `ScanResultaat` — last scan written by PC (int32)
- `ActievePartijnummer1`, `ActievePartijnummer2` — active batch per side (int32)
- `Ziftmaat1`, `Ziftmaat2` — sieve size per side
- `vDummy` — heartbeat / smoke field

Leuze (`opc.tcp://10.0.0.191:4840`):

- `LastScanData` (`ns=5;i=6122`)
- `ScanActive` (`ns=5;i=6199`)
- `DeviceTemperature` (`ns=5;i=6116`)

Node list lives in code as a small constant; adding/removing a node is a code
change, not a config change. Names/IDs match what's already wired in
`scripts/monitor_plc.py` and `scripts/monitor_leuze.py`.

### Out of scope

- Writing to the PLC (separate tool — `scripts/write_plc.py`).
- Protocol state machine, partij lookups, web UI ([[os_pc_protocol_implementation]]).
- Alerting / paging. Logger output is the data source; alerting is downstream.

## TUI

Textual (Textualize). Justification:

- Async, fits the asyncua subscription loop without bridging threads.
- Usable over ssh in a plain tmux pane (no mouse required, but supported).
- Per-source tables are trivial (`DataTable`) and we can add a footer with
  connection status / last-update age without fighting the framework.

Layout sketch:

```
┌─ Potting PLC (10.0.0.190) ─── connected, last upd 0.4s ago ─┐
│ Node                  Value        Server ts                │
│ ScanResultaat         27246        2026-05-21 14:02:11.213  │
│ ActievePartijnummer1  12345        ...                      │
│ ...                                                         │
├─ Leuze (10.0.0.191) ─── connected, last upd 12s ago ────────┤
│ LastScanData          .../27246    ...                      │
│ ...                                                         │
└─ q: quit  l: toggle log tail  r: reconnect ────────────────┘
```

Reconnect on disconnect (with exponential backoff); the footer should always
make stale data obvious.

## Logger

JSON lines, one record per datachange notification:

```json
{"ts":"2026-05-21T14:02:11.213Z","source":"plc","node":"ScanResultaat","value":27246,"server_ts":"...","status":"Good"}
```

- One file per process run, rotated by size (e.g. 50 MB) and date.
- Path configurable via env (`VINEAPP_OPCUA_MONITOR_LOG_DIR`, default
  `/app/logs/opcua/`).
- Log level / which sources to record configurable via env; default = all
  monitored nodes.
- Grep-friendly today; `pandas.read_json(..., lines=True)` later.

## Deployment

- Same container image as the web app (`ghcr.io/serraict/wetering-production-control`).
- New compose service `opcua_monitor` alongside `production_control` and
  `opcua_test`, with the same `env_file` and `certs` volume.
- Entry point: `uv run python -m production_control.opcua.monitor` (TUI) and
  `uv run python -m production_control.opcua.monitor --headless` (logger-only,
  for `docker compose up -d`).

## Testability

- Adapt `scripts/opc_test_server.py` so it exposes the protocol node set above
  (it currently models an older `Lijn{n}/PC/OS` shape — drift from the current
  protocol). Same names/types as the real PLC so the monitor needs no special
  test mode.
- Smoke test: start the test server in a pytest fixture, run the monitor in
  `--headless` mode against it for a few seconds, assert the JSONL log contains
  the expected node names and a value change.
- Manual test via the existing `opcua_test` compose service pattern:
  `docker compose run --rm opcua_test python -m production_control.opcua.monitor --plc-url ...`.

## Open questions

- Where does the monitor run in production — its own container instance on
  `serraserver` (long-running), or only on demand via `docker compose run`?
  Headless logger probably wants long-running; the TUI is on-demand.
- Log retention policy on serraserver — rotate locally only, or ship to an
  external sink?

## Acceptance criteria (proposed)

- [ ] `production_control.opcua.monitor` package with TUI and headless modes.
- [ ] Subscribes to the fixed node set above on both endpoints; survives a
      disconnect/reconnect cycle without crashing.
- [ ] JSONL log written under `VINEAPP_OPCUA_MONITOR_LOG_DIR`, rotated.
- [ ] Smoke test against the test server passes in CI.
- [ ] Compose service added; documented in `docs/architecture.md` and in
      `work/notes/ontstapelmachine/doing_ontstapelaar.md` "Commands to run on
      serraserver".
- [ ] One-page operator doc: how to attach the TUI, how to tail the log.
