# OS ↔ PC Protocol Implementation

Implements the protocol from the [protocol draft] so the Ontstapelaar (OS) and
Production Control (PC) can coordinate a potting run end-to-end. Independent
of, but sharing the OPC/UA plumbing with, [[plc_monitoring_app]].

Builds on the test plan already worked out in
[`ontstapelmachine/archive/os_pc_protocol_test_plan.md`](ontstapelmachine/archive/os_pc_protocol_test_plan.md)
and the field-test state in
[`ontstapelmachine/doing_ontstapelaar.md`](ontstapelmachine/doing_ontstapelaar.md).

## Purpose

Replace the "manual scan → PC writes value → OS reads value" choreography
currently done by scripts (`scripts/write_plc.py`, `scripts/monitor_leuze.py`,
`scripts/monitor_plc.py`) with a single long-running service that owns the
protocol contract.

## Protocol summary

(From the archived test plan — restated here so this note stands alone.)

### PLC nodes (Omron, ns=4)

| Protocol name           | NodeId                       | Type  | Writer |
| ----------------------- | ---------------------------- | ----- | ------ |
| `last_scan_data`        | `ns=4;s=ScanResultaat`       | int32 | PC writes, OS resets to 0 |
| `actieve_partij_nummer_1` | `ns=4;s=ActievePartijnummer1` | int32 | PC writes |
| `actieve_partij_nummer_2` | `ns=4;s=ActievePartijnummer2` | int32 | PC writes |

### Leuze node

- `LastScanData` (`ns=5;i=6122`) — scan URL, batch number = last path segment.

### Happy path

1. OS sets `last_scan_data = 0` → ready for a new scan.
2. Operator scans a pallet on the OS; Leuze publishes the URL on `LastScanData`.
3. PC parses the batch number from the URL.
4. PC writes the batch number to PLC `last_scan_data`.
5. OS reads it, acts, resets `last_scan_data` back to 0.
6. PC may also update `actieve_partij_nummer_{1,2}` to reflect the active batch
   per side; writing `0` signals "no active batch".

### Edge cases worth specifying

- OS never resets to 0 (timeout / stuck) — PC behavior?
- Scan arrives while `last_scan_data != 0` (OS not ready) — buffer? drop? wait?
- Same scan twice in a row — idempotent?
- Unparseable scan (not a `.../potting-lots/scan/<int>` URL) — log & skip?
- Connection drop mid-cycle (PLC or Leuze) — resume rules?
- PC restart with `last_scan_data != 0` — adopt the in-flight value or wait
  for next reset?

These are the cases the behave specs should pin down. Most are still open
questions on the protocol draft — capture decisions in the architecture doc
as they're resolved.

## Where it lives

- Module: `src/production_control/opcua/protocol/` (state machine + parsers).
- Runtime: same container image as the web app, separate compose service
  (`opcua_protocol`), single instance.
- Reads config from the same `VINEAPP_OPCUA_*` env vars as the existing
  scripts.

## Executable spec (behave)

Specs run against `scripts/opc_test_server.py` (real asyncua client ↔ server
traffic). Rationale: the wire-level quirks have bitten us repeatedly (Omron EKU
requirements, Leuze malformed cert, encoding limits) — the spec is most
valuable when it exercises the actual stack.

Required updates to `scripts/opc_test_server.py`:

- Replace the current `Lijn{n}/PC/OS` shape with the current protocol nodes
  (`ScanResultaat`, `ActievePartijnummer1`, `ActievePartijnummer2`,
  `Ziftmaat1`, `Ziftmaat2`, `vDummy`) under `ns=4`.
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
    os_not_ready.feature
    unparseable_scan.feature
    connection_recovery.feature
  environment.py          # starts the test server, the OS simulator, and
                          # a fresh PC protocol instance per scenario
  steps/
    plc_steps.py          # "Given the PLC reports last_scan_data = 0"
    scanner_steps.py      # "When a scan arrives with batch 27246"
    pc_steps.py           # "Then PC writes 27246 to ScanResultaat"
```

Acceptance: `uv run behave features/protocol` runs in CI and locally with no
hardware.

## Documentation

Architecture doc gets a new `## OPC/UA Machine Communication` section
(`docs/architecture.md#opcua-machine-communication`) covering:

- Topology diagram (PC ↔ PLC ↔ Leuze, who writes what).
- Node table (copy of the table above, plus URIs and security policy).
- Protocol state machine (happy path + the resolved edge cases).
- Pointer to the behave specs as the source of truth for behavior.

## Open questions

- Does PC also need to *read* `actieve_partij_nummer_{1,2}` (round-trip
  reconciliation) or is write-only sufficient?
- How does the protocol service interact with the web app — does it write
  scan events somewhere the UI can read (DB, event log)?
- Polling vs. subscription on `ScanResultaat` — test plan note 2026-03-10
  flagged `--watch` polling missing updates. Confirm subscription works
  reliably before committing.

## Acceptance criteria (proposed)

- [ ] `production_control.opcua.protocol` package with a state machine that
      implements the happy path and the edge cases listed above.
- [ ] `scripts/opc_test_server.py` updated to the current protocol shape;
      OS simulator hook present.
- [ ] `features/protocol/` behave suite runs green against the test server,
      covers happy path + each named edge case.
- [ ] `docs/architecture.md#opcua-machine-communication` written and links to
      the behave features.
- [ ] Compose service `opcua_protocol` added; deploys alongside
      `production_control` on serraserver.

[protocol draft]:
  https://potlilium.fibery.io/ICT_Wetering_Potlilium/Actie/Integratie-Onstapelmachine-met-oppotproces-257?sharing-key=0b2ea7ab-9c2d-4ae1-8b2a-c016b2816fa5
