# Doing: OS ↔ PC Protocol v1 — Scan cycle end-to-end

Smallest verifiable cut of the OS ↔ PC protocol. Full contract:
[`docs/protocol.md`](../docs/protocol.md). Full plan:
[`work/notes/os_pc_protocol_implementation.md`](notes/os_pc_protocol_implementation.md).

## Context

The active-partij write path already exists end-to-end
(`web/pages/potting_lots.py` → `potting_lots/active_service.py` →
`potting_lots/line_controller.py` → OPC). But `PottingLineController`
points at the **old** NodeIds (`Lijn{N}_PC_nr_actieve_partij` in
`http://wetering.potlilium.nl/potting-lines`) and uses anonymous
no-security. The new protocol uses `ns=4;s=OPCScanner/fbOPC/
ActievePartijnummer{1,2}` and SignAndEncrypt with user + cert.

The scan half (PC reads Leuze → parses → gated write to
`ns=4;s=OPCScanner/fbOPC/ScanResultaat`) doesn't exist at all.

v1 wires both halves so the protocol works end-to-end **against the test
server**. Wiring into the running web app process and prod verification
are v2.

## Goals

1. `scripts/opc_test_server.py` exposes the new protocol surface and an
   OS-simulator hook (resets `ScanResultaat` to 0 after N ms).
2. New module `src/production_control/opcua/protocol/` implements the
   scan cycle: subscribe to Leuze, parse, gated write to the PLC.
3. `PottingLineController` writes `ActievePartijnummer{1,2}` to the new
   NodeIds, with the same security as the monitor.
4. `features/protocol/scan_cycle.feature` and
   `features/protocol/active_partij.feature` run green via
   `uv run behave features/protocol`. Suite is structured so it can
   eventually replace `docs/protocol.md` as the authoritative spec.

## Acceptance criteria

- [ ] Against the updated test server: send a Leuze scan
      `https://.../potting-lots/scan/27246`; observe PC writes `27246`
      to `ScanResultaat`. After the OS-sim resets it to 0, send another
      scan; PC writes again. Send a scan while `ScanResultaat != 0`; PC
      does NOT write (dropped + logged).
- [ ] Unparseable scan (`"not a url"`, `https://.../other/path`) → PC
      does NOT write; logs at WARNING.
- [ ] Operator activates a partij in the existing potting-lots UI → PLC
      shows the value under the new NodeId. (Verify against test server
      via `monitor_plc`-style read.)
- [ ] `uv run behave features/protocol` passes locally and in CI; no
      hardware required. v1 features: scan_cycle, active_partij.
- [ ] All existing tests (`uv run pytest`) still pass — the
      `PottingLineController` NodeId change doesn't break
      `tests/test_opc_integration.py`.

## Design

### Test server (`scripts/opc_test_server.py`)

Rewrite the node shape to match production:

```
ns=4 (urn:omron:OPCScanner)
  OPCScanner/
    fbOPC/
      ScanResultaat            (Int32, RW)
      ActievePartijnummer1     (Int32, RW)
      ActievePartijnummer2     (Int32, RW)
      AantalBollenPerKrat      (Int32, RW)   # for future bolmaat work
  DeviceStatus/
    Mode                       (String, R)
    ErrorStatus                (String, R)

ns=5 (urn:leuze:DCR202iC)
  i=6122  LastScanData          (String, RW)
```

Drop the old `Lijn{n}/PC/OS` tree entirely; nothing in shipped code
depends on it once `PottingLineController` is updated.

OS simulator: background task that polls `ScanResultaat` every 100 ms;
when it goes non-zero, sleep `--os-ack-delay-ms` (default 500), then
write 0. Flag via env var `OPC_TEST_OS_ACK_DELAY_MS` so the behave
suite can shorten it.

### Protocol module (`src/production_control/opcua/protocol/`)

- `__init__.py` — public surface (`run_scan_cycle`, `main`).
- `scan_parser.py` — `parse_scan(url: str) -> int | None`. Returns the
  trailing integer from `.../potting-lots/scan/<int>`. `None` for
  anything else.
- `scan_cycle.py` — the handler:
  1. Subscribe to Leuze `LastScanData` (reuse `leuze.run_leuze` shape,
     fixed-node subscription).
  2. Subscribe to PLC `ScanResultaat` (track current value).
  3. On Leuze datachange:
     - Parse value; drop+log if `None`.
     - Drop+log if last-known `ScanResultaat != 0` (guard).
     - Write parsed int to `ScanResultaat` (`ns=4;s=OPCScanner/fbOPC/
       ScanResultaat`, `Int32`).
  4. On PLC `ScanResultaat` datachange: update last-known.
- Wrap both subscriptions in `monitor.supervise` for reconnect.
- `main()` — entry point: `python -m production_control.opcua.protocol`.
  Same env-var config as monitor.

The handler interface follows the existing `JsonlHandler` / `StateHandler`
pattern (`.register(node, name)`, `.datachange_notification(node, val,
data)`), so we can plug it into the existing `run_plc` / `run_leuze`
without further refactoring.

### PottingLineController node update

Two changes in `src/production_control/potting_lots/line_controller.py`:

1. Replace the `_node_ids` map and namespace resolution. Switch to the
   protocol NodeIds:
   ```python
   _node_ids = {
       "line1_pc_active": "ns=4;s=OPCScanner/fbOPC/ActievePartijnummer1",
       "line2_pc_active": "ns=4;s=OPCScanner/fbOPC/ActievePartijnummer2",
   }
   ```
   Drop the `line{N}_os_active` and `last_updated` keys — not in the
   protocol surface; nothing reads them in shipped code (verify with
   grep before deleting).
2. Move from anonymous `Client(url=...)` to the `_build_client` /
   `set_security` shape used by the monitor (user + password + client
   cert + `Basic256Sha256` + `SignAndEncrypt`). Read the same
   `VINEAPP_OPCUA_*` env vars; fall back to anonymous when
   `VINEAPP_OPCUA_SECURITY=none` so the test server still works
   in CI.

`tests/test_opc_integration.py` needs the same env to point at the
updated test server. Re-verify these still pass.

### behave suite (`features/protocol/`)

The intent is that this suite eventually replaces `docs/protocol.md` as
the authoritative spec — the scenarios below should read as the
protocol contract, not as test scaffolding. Add scenarios as edges are
discovered so the suite stays the source of truth.

```
features/
  protocol/
    scan_cycle.feature           # ← v1
    active_partij.feature        # ← v1
    edge_cases.feature           # ← v3 (placeholder in v1)
    connection_recovery.feature  # ← v3 (placeholder in v1)
  environment.py    # starts test server in a subprocess per scenario,
                    # waits for endpoint, starts the protocol module,
                    # tears down after
  steps/
    plc_steps.py
    scanner_steps.py
    pc_steps.py
    operator_steps.py
```

Step vocabulary is intentionally domain-level (`a scan arrives with
payload …`, `the operator activates partij … on line …`) so the
scenarios read like protocol prose. Wire-level details (NodeIds,
namespace indexes, security) live in the step definitions and the
`environment.py`, not in the feature files.

#### v1 feature files

`features/protocol/scan_cycle.feature`:

```gherkin
Feature: Scan cycle (PC acknowledges scans from OS)

  PC observes Leuze scans, parses the partij from the scan URL, and
  writes it to ScanResultaat — but only after observing the field equals
  0. OS resets the field to 0 once it has read the value; the guard
  protects against overwriting an unread scan.

  Background:
    Given the PLC reports ScanResultaat = 0
    And the protocol handler is running

  Scenario: PC publishes a parsed partij when the guard allows
    When a scan arrives with payload "https://pc.potlilium.serraict.me/potting-lots/scan/27246"
    Then PC writes 27246 to ScanResultaat

  Scenario: Successive scans cycle through OS acknowledgement
    When a scan arrives with payload ".../potting-lots/scan/27246"
    Then PC writes 27246 to ScanResultaat
    When OS resets ScanResultaat to 0
    And a scan arrives with payload ".../potting-lots/scan/27247"
    Then PC writes 27247 to ScanResultaat

  Scenario: PC drops a scan while the previous one is still unread
    Given the PLC reports ScanResultaat = 27246
    When a scan arrives with payload ".../potting-lots/scan/27247"
    Then PC does not write to ScanResultaat
    And PC logs "scan dropped: guard not zero" at WARNING

  Scenario: A duplicate scan after OS ack writes again
    When a scan arrives with payload ".../potting-lots/scan/27246"
    And OS resets ScanResultaat to 0
    And a scan arrives with payload ".../potting-lots/scan/27246"
    Then PC writes 27246 to ScanResultaat
```

`features/protocol/active_partij.feature`:

```gherkin
Feature: Active partij publication (PC tells OS which lots are live)

  The operator picks one or two active partijen on the potting-lots
  page. PC publishes the IDs to ActievePartijnummer1 / 2 on the PLC.
  OS uses them locally to decide vrijgave. A value of 0 means
  "no active partij" and tells OS to refuse vrijgave.

  Scenario: Operator activates a partij on line 1
    When the operator activates partij 12345 on line 1
    Then PC writes 12345 to ActievePartijnummer1

  Scenario: Operator activates a partij on line 2
    When the operator activates partij 67890 on line 2
    Then PC writes 67890 to ActievePartijnummer2

  Scenario: Operator deactivates a line
    Given partij 12345 is active on line 1
    When the operator deactivates line 1
    Then PC writes 0 to ActievePartijnummer1

  Scenario: Lines are independent
    When the operator activates partij 12345 on line 1
    And the operator activates partij 67890 on line 2
    Then PC writes 12345 to ActievePartijnummer1
    And PC writes 67890 to ActievePartijnummer2
```

#### v3 placeholders (one per file, no `@wip` scenarios yet)

`features/protocol/edge_cases.feature`:

```gherkin
Feature: Scan edge cases

  # v3: covers unparseable scans, repeated scans before ack, the OS
  # never resetting (stuck), and PC restart with ScanResultaat != 0.
  # See docs/protocol.md "Edge cases" until these scenarios land.
```

`features/protocol/connection_recovery.feature`:

```gherkin
Feature: Connection recovery

  # v3: covers PLC and Leuze drops mid-cycle. PC re-reads
  # ScanResultaat on reconnect and only resumes writing when it sees 0.
```

#### What "done" looks like for v1

- `uv run behave features/protocol/scan_cycle.feature` passes.
- `uv run behave features/protocol/active_partij.feature` passes.
- `uv run behave features/protocol` runs the placeholders without
  errors (no scenarios, no failures).
- A note in `docs/protocol.md` pointing at `features/protocol/` as the
  evolving executable spec; the prose contract stays authoritative
  until the suite covers every edge in the "Edge cases" table.

### Explicitly out of scope for v1

- **Wiring into the web app process.** v2 — needs a startup hook that
  runs the protocol task on NiceGUI lifespan. v1 ships the module + the
  test server + the behave spec; we run it standalone for now.
- **Prod verification.** v2 — needs v1 plus the lifespan wiring.
- **Live UI feedback** (show current `ScanResultaat`, last scan time,
  per-line active partij from the PLC). v4.
- **Edge case specs.** v3.
- **bolmaat / AantalBollenPerKrat write path.** Deferred per protocol
  doc; the test server exposes the node so it's ready when we get
  there.
- **`PottingLineController.get_active_lot`** — the controller has read
  paths for `line{N}_os_active`. Since the OS half doesn't exist on
  the real PLC and nothing in shipped UI reads it, delete those code
  paths in this slice (smaller controller, less surface to keep in sync).

## Implementation steps

Each step that lands scenarios lists them; cap is 3 per step so a
failing step has at most 3 things to debug.

- [x] Add `behave` to dev deps (`uv add --dev behave` → behave 1.3.3).

- [ ] **Preconditions — test server + scan parser.** No scenarios yet.
  - Update `scripts/opc_test_server.py`: new node tree (per Design),
    OS sim, configurable ack delay (`OPC_TEST_OS_ACK_DELAY_MS`).
    Sanity check with `uv run python scripts/opc_test_server.py`.
  - `src/production_control/opcua/protocol/scan_parser.py` + unit tests
    in `tests/opcua/test_scan_parser.py`. Cases: valid URL, trailing
    slash, non-int suffix, wrong path, garbage, empty.

- [ ] **First scenario — minimal scan-cycle handler.**
  - `src/production_control/opcua/protocol/scan_cycle.py` with the
    handler skeleton (subscribe Leuze + PLC, write on datachange).
    Reuse `monitor.run_plc` / `leuze.run_leuze` for connection lifecycle.
  - `src/production_control/opcua/protocol/__init__.py` + `main()` so
    `python -m production_control.opcua.protocol` runs against the
    test server.
  - `features/protocol/environment.py` (test-server subprocess + protocol
    module subprocess per scenario) + minimal `steps/{plc,scanner,pc}_steps.py`.
  - `features/protocol/scan_cycle.feature` with Background + first scenario.
  - **Scenarios landed (1):**
    1. `scan_cycle`: *PC publishes a parsed partij when the guard allows*

- [ ] **Scan-cycle: OS-ack and guard-fail.**
  - Extend `pc_steps.py` with the "OS resets ScanResultaat to 0" and
    "PC does not write" / "PC logs at WARNING" steps.
  - **Scenarios landed (2):**
    1. `scan_cycle`: *Successive scans cycle through OS acknowledgement*
    2. `scan_cycle`: *PC drops a scan while the previous one is still unread*

- [ ] **Scan-cycle: duplicates.**
  - No new step vocabulary — should pass on existing steps once the
    handler is correct. If it doesn't, fix the handler, not the test.
  - **Scenarios landed (1):**
    1. `scan_cycle`: *A duplicate scan after OS ack writes again*

- [ ] **`PottingLineController` NodeId update + first active-partij
      scenarios.**
  - Replace `_node_ids` map (drop `line{N}_os_active` + `last_updated`
    after grep-confirming nothing reads them).
  - Switch to env-var-based `_build_client` / `set_security`; fall back
    to anonymous when `VINEAPP_OPCUA_SECURITY=none`.
  - Update `tests/test_opc_integration.py` env so it points at the new
    test server shape; ensure it still passes.
  - `features/protocol/active_partij.feature` + `steps/operator_steps.py`
    (calls `ActivePottingLotService` directly — no NiceGUI in the test).
  - **Scenarios landed (2):**
    1. `active_partij`: *Operator activates a partij on line 1*
    2. `active_partij`: *Operator activates a partij on line 2*

- [ ] **Active-partij: deactivation and independence.**
  - **Scenarios landed (2):**
    1. `active_partij`: *Operator deactivates a line*
    2. `active_partij`: *Lines are independent*

- [ ] **Placeholders, CI, capture.** No scenarios.
  - `features/protocol/edge_cases.feature` and
    `features/protocol/connection_recovery.feature` as v3 placeholders
    (feature description only, zero scenarios — runner stays green).
  - Hook `uv run behave features/protocol` into the Makefile / CI
    target (check pattern alongside `dev-test`).
  - Capture findings in
    `work/notes/ontstapelmachine/protocol_v1_capture.md` (what
    surprised us in the test server, scan-parse edge cases seen,
    anything ugly in the handler). Fold notable ones back into
    `os_pc_protocol_implementation.md`.
  - Add a pointer in `docs/protocol.md` to `features/protocol/` as the
    evolving executable spec.
