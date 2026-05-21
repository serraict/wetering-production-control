# OS ↔ PC Protocol Implementation

Implementation note for the protocol described in
[`docs/protocol.md`](../../docs/protocol.md). Shares OPC/UA plumbing with
[[plc_monitoring_app]] but is otherwise independent. The user-facing
contract (nodes, sequences, edge cases) lives in `docs/protocol.md`;
this note captures the implementation slice plan, the behave spec, and
the open implementation questions.

Builds on the test plan in
[`ontstapelmachine/archive/os_pc_protocol_test_plan.md`](ontstapelmachine/archive/os_pc_protocol_test_plan.md)
and the field-test state in
[`ontstapelmachine/doing_ontstapelaar.md`](ontstapelmachine/doing_ontstapelaar.md).

## Where it lives

- **No separate service.** The web app (NiceGUI process) owns the OPC
  client, matching the architecture-doc model. Adds a long-running
  asyncua subscription loop alongside the request handlers.
- Module: `src/production_control/opcua/protocol/` (Leuze subscription,
  scan parsing, gated write logic, state observers for the UI).
- Reuses the connection + supervisor layer in
  `src/production_control/opcua/monitor.py` and the Leuze source in
  `src/production_control/opcua/leuze.py`.
- Reads config from the same `VINEAPP_OPCUA_*` env vars (see
  [`docs/deployment.md`](../../docs/deployment.md)).
- Operator UI: extend the existing potting-lots page to set
  `actieve_partij_nummer_{1,2}` and to show the live scan/partij state.

## Executable spec (behave)

Specs run against `scripts/opc_test_server.py` (real asyncua client ↔
server traffic). Rationale: the wire-level quirks have bitten us
repeatedly (Omron EKU requirements, Leuze malformed cert, encoding
limits) — the spec is most valuable when it exercises the actual stack.

Required updates to `scripts/opc_test_server.py`:

- Replace the current `Lijn{n}/PC/OS` shape with the three protocol
  nodes under `ns=4`: `ScanResultaat`, `ActievePartijnummer1`,
  `ActievePartijnummer2`.
- Add an OS-simulator hook so the spec can script "OS reads value and
  resets to 0 after N ms" without a real PLC.
- Expose a Leuze-shaped namespace (`ns=5;i=6122` `LastScanData`) on the
  same server (or a sibling server fixture) so PC can subscribe to a
  fake scanner.
- Allow anonymous / no-security on the test endpoint (already the case)
  — no cert work needed for the test path.

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

Acceptance: `uv run behave features/protocol` runs in CI and locally with
no hardware.

## Open questions

- Does PC also need to **read** `actieve_partij_nummer_{1,2}` (round-trip
  reconciliation), or is write-only sufficient given PC is the only writer?
- Polling vs. subscription on `ScanResultaat`: the 2026-03-10 test note
  flagged `--watch` polling missing updates. Confirm subscription is
  reliable before committing to it as the OS-ready signal.

## Acceptance criteria (proposed)

- [ ] `production_control.opcua.protocol` module: Leuze subscription,
      scan parser, gated PLC writer, plus UI hooks to set the active
      partij.
- [ ] `scripts/opc_test_server.py` updated to the three protocol nodes
      plus a Leuze-shaped fixture; OS-simulator hook present.
- [ ] `features/protocol/` behave suite runs green against the test
      server; covers happy path + each named edge case.
