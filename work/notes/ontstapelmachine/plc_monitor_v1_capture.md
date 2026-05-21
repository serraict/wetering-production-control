# PLC Monitor v1 — First Capture on Production

Date: 2026-05-21, on `serraserver` against the production Omron PLC
(`opc.tcp://10.0.0.190:4840`). Captured by running the monitor inside the
`opcua_test` container; ~5 min window, no operator activity (no writes).

## Discovered surface (real PLC)

9 unique variables across two subtrees under `ns=4`:

**`DeviceStatus.*` — operational state of the OPC server / device:**
- `DeviceStatus.Mode` (string) — observed `"RUN"`
- `DeviceStatus.ErrorStatus` (string) — observed `"ContinuousError"` *(unclear
  if this is a steady-state value or a real fault — ask the PLC engineer)*
- `DeviceStatus.UnpublishedVariablesStatus` — `0`

**Meta:**
- `NumOfVars` — `4`
- `NumOfValues` — `4`

**`OPCScanner/fbOPC/*` — the protocol surface and adjacent fields:**
- `ScanResultaat` — `0` (PC writes; OS resets to 0)
- `ActievePartijnummer1` — `0` (PC writes)
- `ActievePartijnummer2` — `0` (PC writes)
- `AantalBollenPerKrat` — `0` (≈ `bolmaat`; see below)

## Surprises vs. the design notes

1. **`AantalBollenPerKrat` exists on the PLC.** Almost certainly the field the
   draft refers to as `bolmaat` (deferred per user on 2026-05-21). It's just
   sitting there waiting; when bolmaat moves out of "deferred" we don't need
   a new PLC variable, only protocol & web-app work.
2. **`Ziftmaat1` / `Ziftmaat2` are NOT exposed.** They were in
   `scripts/write_plc.py` and the doing doc as PLC-internal fields, but the
   live PLC does not publish them under the OPC tree. The monitor note
   already said "do not monitor" — confirmed they're not visible at all,
   not just not in the protocol.
3. **No `vDummy`.** Mentioned in the doing doc as a smoke field; not present
   on the production PLC. Drop from the monitor note (we listed it as an
   "operational extra"; nothing to monitor).
4. **`DeviceStatus.*` is a free observability win.** Mode + ErrorStatus are
   exactly the kinds of fields a monitor should surface. Worth keeping
   visible in the (future) TUI as a header row.

## Bugs found

- **Discovery emitted duplicates.** 14 INFO lines for 9 unique nodes — the
  `DeviceStatus.*` and `NumOf*` are reachable from two top-level Objects
  children, and the `seen` set was created fresh per top-level child instead
  of shared. **Fixed**: share the `seen` set across the `_connect_and_run`
  walk. Confirmed against the test server (no duplicates). Will need a
  redeploy + re-capture on serraserver to confirm against the PLC.

## Wire-level notes

- `Requested session timeout to be 3600000ms, got 60000ms instead` — server
  caps at 60s. asyncua handles keepalive transparently; doesn't matter for
  v1, worth knowing if we ever debug reconnect issues.
- `certificate does not contain the hostname in DNSNames 1a7d89f2b0b5` — that
  hostname is the container's transient id. Cosmetic; no server-side
  rejection.
- `BadNoSubscription` on Ctrl-C — a publish was in flight at shutdown. Pure
  cosmetic; could clean up with a graceful subscription teardown later.
- No actual datachange events during the 5 min window (the line was idle).
  All emitted JSONL records are initial-value snapshots.

## What v1 actually proved

- The discover-and-subscribe approach works against the production Omron
  PLC — 9 variables found, all subscribed, no encoding-limits issues, no
  flood of nodes (the OPC server is curated).
- JSONL output is grep-able and useful as-is.
- Reconnect not yet tested in anger — deferred to a future on-site session
  with the PLC engineer.

## Raw capture (excerpt)

```
2026-05-21 10:01:34,604 INFO opcua_monitor: connecting to opc.tcp://10.0.0.190:4840
2026-05-21 10:01:35,243 WARNING asyncua.client.client: Requested session timeout to be 3600000ms, got 60000ms instead
2026-05-21 10:01:36,132 INFO opcua_monitor: discovered Mode (ns=4;s=DeviceStatus.Mode)
2026-05-21 10:01:36,132 INFO opcua_monitor: discovered ErrorStatus (ns=4;s=DeviceStatus.ErrorStatus)
2026-05-21 10:01:36,132 INFO opcua_monitor: discovered UnpublishedVariablesStatus (ns=4;s=DeviceStatus.UnpublishedVariablesStatus)
2026-05-21 10:01:36,132 INFO opcua_monitor: discovered NumOfVars (ns=4;s=NumOfVars)
2026-05-21 10:01:36,132 INFO opcua_monitor: discovered NumOfValues (ns=4;s=NumOfValues)
2026-05-21 10:01:36,132 INFO opcua_monitor: discovered AantalBollenPerKrat (ns=4;s=OPCScanner/fbOPC/AantalBollenPerKrat)
2026-05-21 10:01:36,132 INFO opcua_monitor: discovered ActievePartijnummer1 (ns=4;s=OPCScanner/fbOPC/ActievePartijnummer1)
2026-05-21 10:01:36,132 INFO opcua_monitor: discovered ActievePartijnummer2 (ns=4;s=OPCScanner/fbOPC/ActievePartijnummer2)
2026-05-21 10:01:36,132 INFO opcua_monitor: discovered ScanResultaat (ns=4;s=OPCScanner/fbOPC/ScanResultaat)
2026-05-21 10:01:36,133 INFO opcua_monitor: discovered Mode (ns=4;s=DeviceStatus.Mode)            <-- dup
2026-05-21 10:01:36,133 INFO opcua_monitor: discovered ErrorStatus (ns=4;s=DeviceStatus.ErrorStatus)  <-- dup
2026-05-21 10:01:36,133 INFO opcua_monitor: discovered UnpublishedVariablesStatus (...)            <-- dup
2026-05-21 10:01:36,133 INFO opcua_monitor: discovered NumOfVars (ns=4;s=NumOfVars)                <-- dup
2026-05-21 10:01:36,133 INFO opcua_monitor: discovered NumOfValues (ns=4;s=NumOfValues)            <-- dup
2026-05-21 10:01:36,155 INFO opcua_monitor: subscribed to 14 variables
{"ts": "2026-05-21T10:01:36.641526+00:00", "source": "plc", "node_id": "ns=4;s=DeviceStatus.Mode", "node": "Mode", "value": "RUN", ...}
{"ts": "2026-05-21T10:01:36.641658+00:00", "source": "plc", "node_id": "ns=4;s=DeviceStatus.ErrorStatus", "node": "ErrorStatus", "value": "ContinuousError", ...}
...
```

## Open questions for the PLC engineer (on-site)

- Is `DeviceStatus.ErrorStatus == "ContinuousError"` the steady-state value,
  or a real fault we should chase?
- Confirm: `AantalBollenPerKrat` is the PLC's existing slot for what the
  draft calls `bolmaat` — i.e. when we wire bolmaat, we should write to that
  variable, not create a new one?
- What is `UnpublishedVariablesStatus` actually counting? Useful as a
  monitor signal or noise?
