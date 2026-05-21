# Doing: PLC Monitor v2 — Leuze

Add the Leuze scanner as a second source on the existing monitor. Smallest
useful slice of [[plc_monitoring_app]] after v1.

Full note: [`work/notes/plc_monitoring_app.md`](notes/plc_monitoring_app.md).

## Context

v1 streams JSONL from the production PLC and runs cleanly. The Leuze scanner
exposes the actual scan data (which OS↔PC protocol work will later consume),
so it's the next data source worth pulling into the same stream. Scope after
this: v3 Textual TUI, v4 file logging, v5 persistent service (or replaced by
a cron/background command on the server — decide then).

We already have `scripts/monitor_leuze.py` proving the Leuze connection
works on-device, including the LenientCertificate monkey-patch for the
malformed server certificate and the fixed-list workaround for
`BadEncodingLimitsExceeded` when subscribing to the full browse tree.

## Goals

1. Subscribe to the fixed Leuze node set and emit on the same JSONL stream
   as the PLC, tagged with `"source": "leuze"`.
2. PLC and Leuze are independent — one failing doesn't stop the other.

## Acceptance criteria

- [ ] `python -m production_control.opcua.monitor` connects to **both** the
      PLC and the Leuze scanner, subscribes to each, and emits one combined
      JSONL stream (`"source": "plc"` vs `"source": "leuze"`).
- [ ] Each source is supervised independently: if Leuze is unreachable, the
      monitor logs a WARNING and keeps trying; PLC keeps streaming. Same
      the other way around.
- [ ] On disconnect, each source's reconnect loop runs the same 5s retry
      pattern v1 already has.
- [ ] Capture the first multi-source run on serraserver to
      `work/notes/ontstapelmachine/plc_monitor_v2_capture.md` — confirm
      both `"source"` values appear, no surprises.

## Design

- New module `production_control/opcua/leuze.py`:
  - `subscribe_leuze(handler, *, url, user, password, cert, key)` that
    opens a Leuze client, applies the LenientCertificate monkey-patch from
    `scripts/browse_leuze.py`, subscribes to the three fixed node IDs, and
    feeds notifications into the supplied `JsonlHandler`.
  - Fixed node IDs: `ns=5;i=6122` (LastScanData), `ns=5;i=6199`
    (ScanActive), `ns=5;i=6116` (DeviceTemperature). Same as
    `scripts/monitor_leuze.py`.
- `monitor.py` `main()`:
  - Spawn one task per source via `asyncio.create_task`; each task is the
    existing reconnect-loop wrapped around a single-source connect.
  - Use `asyncio.gather(..., return_exceptions=True)` at the top level so a
    crash in one source's loop doesn't kill the other.
  - If the Leuze env vars are unset (e.g. local dev against
    `opc_test_server.py`), log INFO and skip the Leuze task — don't fail.
- `JsonlHandler` already takes `source` per instance — no change.
- Reuse the `VINEAPP_OPCUA_SECURITY=none` override only on the PLC path; the
  Leuze always uses cert + user (that's how it's configured on-device).

### Explicitly out of scope for v2

- File logging — v4.
- Long-running compose service — v5.
- Textual TUI — v3.
- Per-node update-rate cap — only if we see a chatty node.

## Implementation steps

- [ ] `production_control/opcua/leuze.py` with `subscribe_leuze` and the
      LenientCertificate workaround.
- [ ] Refactor `monitor.py`: split the PLC-specific connect loop into its
      own coroutine; introduce a top-level task supervisor that runs PLC +
      Leuze concurrently and handles "Leuze unset → skip" cleanly.
- [ ] Local sanity check: run against `opc_test_server.py` with
      `VINEAPP_OPCUA_SECURITY=none` and no `VINEAPP_OPCUA_LEUZE_URL` —
      confirm the PLC stream still works and "leuze not configured, skipping"
      shows up in stderr.
- [ ] Build + push image (`make docker_push`).
- [ ] On serraserver:
      `docker compose run --rm opcua_test python -m production_control.opcua.monitor`
      against both production endpoints; capture 5–10 minutes to
      `work/notes/ontstapelmachine/plc_monitor_v2_capture.md`.
- [ ] Review the capture: do we see Leuze records? Any surprises (cert
      issue, encoding limits, chatty nodes)? Fold findings into
      [`work/notes/plc_monitoring_app.md`](notes/plc_monitoring_app.md).
