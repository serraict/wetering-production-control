# OS ↔ PC Protocol (Ontstapelaar)

How Production Control (**PC**) and the Ontstapelaar (**OS**) coordinate
the potting run over OPC/UA.

- **OS** scans each krat on pickup, tracks its partij, and decides
  *vrijgave* (release to be emptied) locally by comparing the scanned
  partij to the active partij values that PC publishes.
- **PC** publishes which oppot partij is active (operator action in the
  web UI) and acknowledges scans by writing the parsed partij back to the
  PLC.

There is no explicit "release" message — release is implicit: when an
active-partij slot contains the scanned partij, OS may empty the krat.

## Endpoints

| Role  | Endpoint                          | Auth                                  |
| ----- | --------------------------------- | ------------------------------------- |
| PLC   | `opc.tcp://10.0.0.190:4840`       | User + client cert (SignAndEncrypt)   |
| Leuze | `opc.tcp://10.0.0.191:4840`       | User + client cert (SignAndEncrypt)   |

Security policy: `Basic256Sha256`, mode `SignAndEncrypt`. The Leuze
scanner's server certificate is non-standard and requires the
`LenientCertificate` lenient parser; see
`src/production_control/opcua/leuze.py`. The PLC user is restricted to the
protocol nodes (PLC-side access control, 2026-05-12).

Connection settings come from `VINEAPP_OPCUA_*` env vars — see
[`deployment.md`](deployment.md).

## Nodes

### PLC (Omron, `ns=4`)

| Protocol name             | NodeId                                          | Type  | Writer                         |
| ------------------------- | ----------------------------------------------- | ----- | ------------------------------ |
| `last_scan_data`          | `ns=4;s=OPCScanner/fbOPC/ScanResultaat`         | int32 | PC writes, OS resets to 0      |
| `actieve_partij_nummer_1` | `ns=4;s=OPCScanner/fbOPC/ActievePartijnummer1`  | int32 | PC writes (on operator action) |
| `actieve_partij_nummer_2` | `ns=4;s=OPCScanner/fbOPC/ActievePartijnummer2`  | int32 | PC writes (on operator action) |

`0` is the sentinel: in `last_scan_data` it means "OS ready for new
data"; in `actieve_partij_nummer_*` it means "no active partij".

### Leuze scanner (`ns=5`)

| Protocol name    | NodeId            | Type   | Notes                                |
| ---------------- | ----------------- | ------ | ------------------------------------ |
| `LastScanData`   | `ns=5;i=6122`     | string | Scan URL; batch = last path segment  |

Example payload: `https://pc.potlilium.serraict.me/potting-lots/scan/27246`.

### Deferred / out of scope

- `bolmaat` (int32, PC → OS, `0 = onbekend`) — listed in the protocol
  draft; not exchanged in this iteration. The PLC already exposes a slot
  for it as `AantalBollenPerKrat` (under `OPCScanner/fbOPC/`) — when
  `bolmaat` lands, PC writes there.
- `Ziftmaat1`, `Ziftmaat2`, `vDummy` — referenced in old notes but **not
  exposed** by the production PLC. Do not read or write.

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

**Key invariant: PC only writes `last_scan_data` after observing it
equals 0.** That guards against overwriting an unread scan.

### Active partij update (operator-driven)

PC writes `actieve_partij_nummer_{1,2}` whenever the operator changes the
active partij(en) in the web UI. Writing `0` signals "no active partij"
and OS will refuse vrijgave for any subsequent scan. Independent of the
scan cycle.

## Edge cases

| Situation                                       | PC behavior                                                  |
| ----------------------------------------------- | ------------------------------------------------------------ |
| OS never resets `last_scan_data` to 0 (stuck)   | Surface in UI; do not auto-recover.                          |
| Scan arrives while `last_scan_data != 0`        | Do not write. Drop the late scan and log it.                 |
| Same scan twice in a row                        | Gated by the `== 0` guard — repeat after OS ack is fine.     |
| Unparseable scan (not a `.../scan/<int>` URL)   | Log and skip. Do not touch the PLC.                          |
| Connection drop mid-cycle (PLC or Leuze)        | On reconnect, re-read `last_scan_data`; resume cleanly if 0. |
| PC restart with `last_scan_data != 0`           | Adopt the value as in-flight; do not overwrite.              |

## Manual fallback (commissioning / troubleshooting)

Per the protocol draft's "Eerste oplossing": OS runs without the scanner
and the operator approves vrijgave manually on the machine UI. This mode
does not involve PC; the protocol implementation only needs to be aware
that OS may be in manual mode (no scans arrive). No code change.

## Where this lives in PC

The web app (NiceGUI process) owns the OPC client. The same module that
runs the long-running asyncua subscription loop also exposes the operator
UI for setting `actieve_partij_nummer_{1,2}`.

- Connection layer + reconnect supervisor + handler abstraction:
  `src/production_control/opcua/monitor.py`.
- Leuze source + cert workaround: `src/production_control/opcua/leuze.py`.
- Protocol layer (scan parsing, gated PLC write, operator-facing
  active-partij writes): `src/production_control/opcua/protocol/`
  (scan-cycle handler) and
  `src/production_control/potting_lots/line_controller.py`
  (active-partij writer). v1 shipped surprises captured in
  [`work/notes/ontstapelmachine/protocol_v1_capture.md`](../work/notes/ontstapelmachine/protocol_v1_capture.md).

The behave executable spec lives at [`features/protocol/`](../features/protocol/)
and runs against `scripts/opc_test_server.py`. As of v1 it covers the
scan cycle (happy path, OS-ack cycle, drop-while-not-zero,
duplicate-after-ack) and active-partij writes (activate per line,
deactivate, line independence) — 8 scenarios across `scan_cycle.feature`
and `active_partij.feature`. Edge cases and connection recovery are v3
placeholders (`edge_cases.feature`, `connection_recovery.feature`). Run
locally with `make behave`; CI runs it as part of `make quality`. The
intent is that this spec eventually supplants the prose above as the
authoritative protocol contract.

## Related

- Operational deployment + cert rotation: [`deployment.md`](deployment.md).
- System-level diagram: [`architecture.md`](architecture.md).
- Field-test status and on-site commands:
  [`work/notes/ontstapelmachine/doing_ontstapelaar.md`](../work/notes/ontstapelmachine/doing_ontstapelaar.md).
- Protocol draft (Fibery, authoritative source of intent):
  [Integratie-Onstapelmachine-met-oppotproces-257](https://potlilium.fibery.io/ICT_Wetering_Potlilium/Actie/Integratie-Onstapelmachine-met-oppotproces-257?sharing-key=0b2ea7ab-9c2d-4ae1-8b2a-c016b2816fa5).
