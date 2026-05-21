# PLC Monitor v2 — Capture & Findings

Date: 2026-05-21, on serraserver. Same `docker compose run --rm opcua_test`
pattern as v1.

## What v2 added

- Leuze scanner as a second supervised source on the same JSONL stream
  (`"source": "leuze"`).
- Independent reconnect supervision: one source's failure doesn't affect the
  other.
- Exponential backoff per source (5s → 10s → 20s → 40s, cap 60s) with a
  give-up threshold after 10 consecutive failures. Reset on a healthy run
  ≥60s. Added because the Leuze was off during the first v2 run and the old
  fixed-5s retry would have log-spammed forever.
- Two PLC discovery bugs surfaced and fixed:
  1. Dedup-vs-depth interaction: shared `seen` across top-level walks pruned
     the short path to `OPCScanner/fbOPC/*`, leaving 5 vars instead of 9.
     Now: walk each top-level subtree with its own `seen`, dedupe by NodeId
     at the end. `MAX_BROWSE_DEPTH` bumped 6 → 20 since the long path needs
     8.
  2. Supervisor logged `exc` directly; some exceptions stringify empty.
     Now logs `type(exc).__name__` + `repr(exc)`, exposing the real
     `TimeoutError` that diagnosed "Leuze is off".

## PLC outcome

- 9 unique variables discovered, all subscribed, JSONL stream healthy.
  Identical surface to v1 (the dedup fix landed; the depth fix recovered
  what the first attempt at dedup had broken).

## Leuze outcome

- Scanner was powered off during the run. Saw `TimeoutError` per attempt,
  with the backoff escalating cleanly: 5s → 10s → 20s → 40s in the first
  ~75 seconds. Would continue to 60s × 6 then give up at ~7 min.
- **End-to-end Leuze + PLC capture deferred** until the scanner is back on.
  Pattern is the same as v1 — `docker compose run --rm` against both
  endpoints, capture for 5–10 minutes, drop the output here as
  `plc_monitor_v2_full_capture.md`.

## Open questions remaining

(Same set as v1, none closed by v2.)

- Is `DeviceStatus.ErrorStatus == "ContinuousError"` the steady-state value
  or a real fault?
- Confirm: `AantalBollenPerKrat` is the PLC's slot for what the draft calls
  `bolmaat`?
- What does `UnpublishedVariablesStatus` actually count?
