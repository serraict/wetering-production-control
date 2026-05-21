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

### Monitored nodes

**PLC (`opc.tcp://10.0.0.190:4840`): discover everything in the user
namespaces, monitor all variables.** On startup the monitor browses the user
namespaces (skipping the OPC-UA standard `Server` / type tree) and subscribes
to every primitive variable it finds. New PLC variables that appear after a
restart get picked up automatically.

Confirmed against the production PLC on 2026-05-21 (see
[`ontstapelmachine/plc_monitor_v1_capture.md`](ontstapelmachine/plc_monitor_v1_capture.md)) —
9 unique variables across two subtrees:

- *Protocol surface (under `OPCScanner/fbOPC/`):* `ScanResultaat`,
  `ActievePartijnummer1`, `ActievePartijnummer2`, plus `AantalBollenPerKrat`
  (the PLC's existing slot for what the draft calls `bolmaat` — deferred from
  the protocol but already a monitor signal).
- *Operational:* `DeviceStatus.{Mode, ErrorStatus, UnpublishedVariablesStatus}`,
  `NumOfVars`, `NumOfValues`.

`Ziftmaat1/2` and `vDummy` are **not** exposed on the production PLC
(contradicting earlier notes) — nothing to do, the discovery walker just won't
see them.

**Leuze (`opc.tcp://10.0.0.191:4840`): fixed curated list.** Subscribing to
the full browse tree fails with `BadEncodingLimitsExceeded` on this device
(confirmed on firmware V2.4.0). Monitor a small fixed set:

- `LastScanData` (`ns=5;i=6122`) — scan URL
- `ScanActive` (`ns=5;i=6199`)
- `DeviceTemperature` (`ns=5;i=6116`)

Adding/removing a Leuze node is a code change; the PLC list is whatever the
PLC currently exposes.

Reference: existing wiring in `scripts/monitor_plc.py` and
`scripts/monitor_leuze.py`.

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
┌─ Potting PLC (10.0.0.190) ─── connected, Mode RUN, last upd 0.4s ago ─┐
│ Node                       Value        Server ts                     │
│ ScanResultaat              27246        2026-05-21 14:02:11.213       │
│ ActievePartijnummer1       12345        ...                           │
│ ActievePartijnummer2       0            ...                           │
│ AantalBollenPerKrat        80           ...                           │
│ DeviceStatus.ErrorStatus   None         ...                           │
│ ...                                                                   │
├─ Leuze (10.0.0.191) ─── connected, last upd 12s ago ──────────────────┤
│ LastScanData               .../27246    ...                           │
│ ...                                                                   │
└─ q: quit  l: toggle log tail  r: reconnect ──────────────────────────┘
```

`DeviceStatus.Mode` and `DeviceStatus.ErrorStatus` are good candidates for the
header row (always visible) rather than just another table entry.

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

- Adapt `scripts/opc_test_server.py` so it exposes a handful of variables in
  a user namespace (it currently models an older `Lijn{n}/PC/OS` shape).
  Exact node names don't matter — the monitor discovers whatever's there.
- Smoke test: start the test server in a pytest fixture, run the monitor in
  `--headless` mode against it for a few seconds, assert the JSONL log
  contains every variable the test server exposed (proving discovery worked)
  and at least one value change.
- Manual test via the existing `opcua_test` compose service pattern:
  `docker compose run --rm opcua_test python -m production_control.opcua.monitor --plc-url ...`.

## Open questions

- Where does the monitor run in production — its own container instance on
  `serraserver` (long-running), or only on demand via `docker compose run`?
  Headless logger probably wants long-running; the TUI is on-demand.
- Log retention policy on serraserver — rotate locally only, or ship to an
  external sink?
- **Discovery filter:** OPC-UA servers expose a large `Server` / type tree
  by default. Plan is to walk only user namespaces (`namespace_index > 0`,
  skipping `http://opcfoundation.org/...`) — confirm that's the right cut
  on the production Omron.
- **Chatty-node guard:** if a single PLC variable updates many times per
  second, the TUI and the JSONL log could be overwhelmed. Worth a
  per-node update-rate cap (sampling interval) or a "noisy nodes" exclude
  list? Defer until we see it happen.

## Acceptance criteria (proposed)

- [ ] `production_control.opcua.monitor` package with TUI and headless modes.
- [ ] **PLC discovery:** on connect, browses the user namespaces, subscribes
      to every primitive variable found; new variables appear automatically
      on the next reconnect.
- [ ] **Leuze:** subscribes to the fixed three-node list.
- [ ] Survives a disconnect/reconnect cycle without crashing.
- [ ] JSONL log written under `VINEAPP_OPCUA_MONITOR_LOG_DIR`, rotated.
- [ ] Smoke test against the test server passes in CI (proves discovery).
- [ ] Compose service added; documented in `docs/architecture.md` and in
      `work/notes/ontstapelmachine/doing_ontstapelaar.md` "Commands to run on
      serraserver".
- [ ] One-page operator doc: how to attach the TUI, how to tail the log.
