# Doing

## Context

The protocol now publishes `AantalBollenPerKrat` (bulb count per krat)
to the PLC on each scan ack. The eventual value will be looked up from
the bollen-picklist for the scanned partij; the actual lookup path is
still TBD with the PLC engineer / Wetering. For now PC writes a
constant `600` via a single function seam so we can swap the source in
without touching the protocol write path.

See `docs/protocol.md` (PLC nodes table + scan-cycle diagram).

## Goals

1. PC writes `AantalBollenPerKrat` to the PLC on every scan ack.
2. The value is produced by `bollen_per_krat_for(partij)` (currently
   returns 600). One callsite, easy to replace later.
3. **Invariant: when OS observes a non-zero `ScanResultaat`, all paired
   information fields (i.e. `AantalBollenPerKrat`) already contain the
   valid values for that scan.** Achieved by writing
   `AantalBollenPerKrat` *before* `ScanResultaat`.
4. Same guard discipline as `ScanResultaat`: no write if the
   `ScanResultaat == 0` guard fails.

## Acceptance criteria

- [ ] On a successful scan, the test server sees both
      `AantalBollenPerKrat = 600` and `ScanResultaat = <partij>`, with
      `AantalBollenPerKrat` written first.
- [ ] On a dropped scan (guard non-zero), neither field is written.
- [ ] Behave feature `scan_cycle.feature` covers both the happy path
      and the dropped-scan case for the paired write.
- [ ] `make quality` is green.

## Design

- New node id constant `PLC_AANTAL_BOLLEN_NODEID` next to the existing
  one.
- New free function `bollen_per_krat_for(partij: int) -> int` (the
  seam). Returns 600.
- `ScanCycleHandler`:
  - Register the new node in `register(...)` next to ScanResultaat.
  - In `_write`: write `AantalBollenPerKrat` first, then
    `ScanResultaat`. Both with explicit `DataValue` to avoid the Omron
    NX timestamp rejection (same workaround we already apply).
- Behave: new `Then` step asserting on the paired field; reuse the
  same wait loop pattern. The ordering invariant is naturally
  enforced by reading `AantalBollenPerKrat` once the `ScanResultaat`
  becomes non-zero — at that moment, the bulb count must already
  match the expected value.

## Implementation steps

- [ ] Add `PLC_AANTAL_BOLLEN_NODEID` and `bollen_per_krat_for(...)` in
      `scan_cycle.py`; export from `protocol/__init__.py`.
- [ ] Wire the new node through `ScanCycleHandler.register` and
      `_write`; write order: bollen → scan.
- [ ] Extend `_plc_loop` to also subscribe/register the new node (we
      don't need to track its value, but the handler needs the Node
      handle for writes).
- [ ] Add a `Then PC writes N to AantalBollenPerKrat` step in
      `features/protocol/steps/plc_steps.py` plus assertion that the
      value is set whenever the scan succeeds.
- [ ] Extend `scan_cycle.feature`: assert the paired write on the
      happy path; assert no paired write on the dropped-scan path.
- [ ] `make quality` green.
