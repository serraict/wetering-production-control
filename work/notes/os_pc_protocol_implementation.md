# OS ↔ PC Protocol Implementation

Implements the protocol from the [protocol draft] so the Ontstapelaar (OS) and
Production Control (PC) coordinate the potting run: PC tells OS which partij is
active and which scan it just observed; OS uses that to decide whether to empty
a krat. Shares OPC/UA plumbing with [[plc_monitoring_app]] but is otherwise
independent.

Builds on the test plan in
[`ontstapelmachine/archive/os_pc_protocol_test_plan.md`](ontstapelmachine/archive/os_pc_protocol_test_plan.md)
and the field-test state in
[`ontstapelmachine/doing_ontstapelaar.md`](ontstapelmachine/doing_ontstapelaar.md).

## Responsibility model

Per the draft:

- **OS** scans the krat on pickup and tracks its partij; OS makes the
  vrijgave decision locally by comparing the scanned partij against the
  PC-published `actieve_partij_nummer_{1,2}`.
- **PC** registers which oppot partij is active (operator action in the web
  UI) and acknowledges scans by writing the parsed partij back to
  `last_scan_data`.

There is no explicit "release" message. Release is implicit: when
`actieve_partij_nummer_{1,2}` contains the scanned partij, OS may empty the
krat.

## Protocol surface

### PLC nodes (Omron, `ns=4`)

| Protocol name             | NodeId                            | Type  | Writer                        |
| ------------------------- | --------------------------------- | ----- | ----------------------------- |
| `last_scan_data`          | `ns=4;s=OPCScanner/fbOPC/ScanResultaat`        | int32 | PC writes, OS resets to 0     |
| `actieve_partij_nummer_1` | `ns=4;s=OPCScanner/fbOPC/ActievePartijnummer1` | int32 | PC writes (on operator action)|
| `actieve_partij_nummer_2` | `ns=4;s=OPCScanner/fbOPC/ActievePartijnummer2` | int32 | PC writes (on operator action)|

`0` is the sentinel: in `last_scan_data` it means "OS ready for new data"; in
`actieve_partij_nummer_*` it means "no active partij".

### Leuze node

- `LastScanData` (`ns=5;i=6122`, string) — scan URL, batch number = last path
  segment (e.g. `https://pc.potlilium.serraict.me/potting-lots/scan/27246`).

### Deferred (not in initial scope, per user 2026-05-21)

- `bolmaat` (int32, PC → OS, `0 = onbekend`) — listed in the protocol draft;
  not exchanged in this iteration.
- `Ziftmaat1/2` — present on the production PLC today, not part of the protocol
  surface; do not write or read.

## Sequences

### Scan cycle (one krat)

```
OS                 PLC (PC)                 Leuze                 PC
 |  (portaal pakt krat)
 | ────────────────▶  last_scan_data := 0
 |  triggers scan ───────────────────────▶
 |                                          publishes LastScanData ─▶
 |                   reads last_scan_data 0 ◀────────────────────────  (guard)
 |                   last_scan_data := parsed_partij ◀─────────────── (PC writes)
 |  reads non-zero ◀
 |  decides vrijgave locally
 |    (parsed_partij ∈ {actieve_partij_1, actieve_partij_2}?)
```

Key: **PC only writes `last_scan_data` after observing it equals 0.** That
guards against overwriting an unread scan.

### Active partij update (operator-driven)

PC writes `actieve_partij_nummer_{1,2}` whenever the operator changes the
active partij(en) in the web UI. Writing `0` signals "no active partij" and
will cause OS to refuse vrijgave for any subsequent scan.

This is independent of the scan cycle.

## Edge cases to specify

(Most still open on the protocol draft — capture decisions as they're resolved.)

- **OS never resets `last_scan_data` to 0** (stuck) — PC behavior: probably
  surface in UI, don't auto-recover. To confirm.
- **Scan arrives while `last_scan_data != 0`** — PC must NOT write; the guard
  exists for this. Question: buffer the late scan, drop it, or wait until OS
  acks? Default: drop and log.
- **Same scan twice in a row** (Leuze re-publishes identical value) — PC
  must still gate on `last_scan_data == 0` so a repeat after OS ack is fine,
  and a repeat before OS ack is dropped.
- **Unparseable scan** (not a `.../potting-lots/scan/<int>` URL) — log & skip;
  don't touch the PLC.
- **Connection drop mid-cycle** (PLC or Leuze) — on reconnect, re-read
  `last_scan_data`; resume cleanly if it's 0, else wait.
- **PC restart with `last_scan_data != 0`** — adopt the value as in-flight;
  don't overwrite. Next write follows the normal guard.

## Where it lives

- **No separate service.** The web app (NiceGUI process) owns the OPC client,
  matching the architecture-doc model (`PottingLineController`, `OPCConfig`).
  Adds a long-running asyncua subscription loop alongside the request handlers.
- Module: `src/production_control/opcua/protocol/` (Leuze subscription, scan
  parsing, gated write logic, state observers for the UI).
- Reads config from the same `VINEAPP_OPCUA_*` env vars as the scripts.
- Operator UI: extend the existing potting-lots page to set
  `actieve_partij_nummer_{1,2}` and to show the live scan/partij state.

### Manual fallback (commissioning / troubleshooting)

Per the draft's "Eerste oplossing": OS runs without the scanner and the
operator approves vrijgave manually on the machine UI. This mode does not
involve PC at all; the protocol implementation only needs to be aware that the
OS may be in manual mode (no scans arrive). No code change required, just a
note in operator docs.

## Executable spec (behave)

Specs run against `scripts/opc_test_server.py` (real asyncua client ↔ server
traffic). Rationale: the wire-level quirks have bitten us repeatedly (Omron EKU
requirements, Leuze malformed cert, encoding limits) — the spec is most
valuable when it exercises the actual stack.

Required updates to `scripts/opc_test_server.py`:

- Replace the current `Lijn{n}/PC/OS` shape with the three protocol nodes
  under `ns=4`: `ScanResultaat`, `ActievePartijnummer1`, `ActievePartijnummer2`.
- Add an OS-simulator hook so the spec can script "OS reads value and resets
  to 0 after N ms" without a real PLC.
- Expose a Leuze-shaped namespace (`ns=5;i=6122` `LastScanData`) on the same
  server (or a sibling server fixture) so PC can subscribe to a fake scanner.
- Allow anonymous / no-security on the test endpoint (already the case) — no
  cert work needed for the test path.

Behave layout:

```
features/
  protocol/
    happy_path.feature
    os_not_ready.feature        # scan while last_scan_data != 0
    unparseable_scan.feature
    repeated_scan.feature
    connection_recovery.feature
  environment.py                # starts the test server, the OS simulator,
                                # and a fresh PC instance per scenario
  steps/
    plc_steps.py                # "Given the PLC reports last_scan_data = 0"
    scanner_steps.py            # "When a scan arrives with batch 27246"
    pc_steps.py                 # "Then PC writes 27246 to ScanResultaat"
```

Acceptance: `uv run behave features/protocol` runs in CI and locally with no
hardware.

## Documentation

`docs/architecture.md#opcua-machine-communication` already exists; extend it
with:

- Topology diagram (PC ↔ PLC ↔ Leuze, who writes what).
- Node table (copy of the table above, plus URIs and security policy).
- Protocol sequence diagrams (scan cycle + active-partij update).
- Manual fallback mode note.
- Pointer to the behave specs as the source of truth for behavior.

## Open questions

- Does PC also need to **read** `actieve_partij_nummer_{1,2}` (round-trip
  reconciliation), or is write-only sufficient given PC is the only writer?
- Polling vs. subscription on `ScanResultaat`: the 2026-03-10 test note
  flagged `--watch` polling missing updates. Confirm subscription is reliable
  before committing to it as the OS-ready signal.

## Acceptance criteria (proposed)

- [ ] `production_control.opcua.protocol` module: Leuze subscription, scan
      parser, gated PLC writer, plus UI hooks to set the active partij.
- [ ] `scripts/opc_test_server.py` updated to the three protocol nodes plus a
      Leuze-shaped fixture; OS-simulator hook present.
- [ ] `features/protocol/` behave suite runs green against the test server;
      covers happy path + each named edge case.
- [ ] `docs/architecture.md#opcua-machine-communication` extended with the
      topology, node table, sequence diagrams, and manual-fallback note.

[protocol draft]:
  https://potlilium.fibery.io/ICT_Wetering_Potlilium/Actie/Integratie-Onstapelmachine-met-oppotproces-257?sharing-key=0b2ea7ab-9c2d-4ae1-8b2a-c016b2816fa5
