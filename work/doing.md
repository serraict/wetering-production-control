# Doing

## Context

`protocol/scan_cycle.py:run_protocol` runs `_plc_loop` and `_leuze_loop`
under `asyncio.gather`. Any unhandled exception in one loop (e.g. Leuze
unreachable, asyncua `set_security` timing out during endpoint probe)
cancels the other through `gather`, the daemon exits, and Docker
crash-loops. We have a `supervise()` wrapper in `monitor.py` that already
solves this for the headless monitor + TUI.

## Goals

Each role in the protocol daemon survives independently — a Leuze
outage must not stop the PLC loop, and vice versa.

## Acceptance criteria

- [x] `_plc_loop` and `_leuze_loop` each run inside `supervise(...)`.
- [x] The protocol daemon never "gives up" — backoff forever (Docker
      `restart: unless-stopped` handles "process truly broken").
- [x] Unit test: when `_leuze_loop` keeps raising, `_plc_loop` stays
      running and Leuze retries.
- [x] `features/protocol` behave suite still green (run_protocol's
      ready/stop_event contract is preserved for the harness).

## Design

- `supervise(name, run, *, max_attempts=RECONNECT_MAX_ATTEMPTS,
  stop_event=None)`:
  - `max_attempts=None` disables giveup.
  - `stop_event` (if provided) is checked after a clean `run()` return
    so graceful shutdown doesn't trigger a misleading "reconnecting"
    log + sleep.
- `run_protocol` wraps each loop in `supervise(..., max_attempts=None,
  stop_event=stop_event)` and `await`s them via `asyncio.gather`. The
  loops keep their `stop_event.wait()` body, so cancellation /
  `stop_event.set()` ends both cleanly.

## Implementation steps

- [x] Add `max_attempts` and `stop_event` parameters to `supervise`.
- [x] Rewire `run_protocol` to use `supervise` per role.
- [x] Add `tests/opcua/test_protocol_supervisor.py` with the Leuze-fail
      / PLC-survives test.
- [x] `make quality`.

## Capture

- One non-obvious bit surfaced during testing: the original `stop_event`
  check only fired on the *clean-return* branch of `supervise`. When the
  Leuze fake kept raising, supervise stayed in the `except` branch and
  the backoff `asyncio.sleep` never noticed shutdown — graceful stop
  hung past the test timeout. Fix: also check `stop_event` after the
  except branch and race the sleep against `stop_event.wait()` via
  `asyncio.wait_for`. Worth remembering if we ever rework supervise's
  shutdown semantics.
- Deferred: nothing planned here, but the long-form item in
  `work/backlog.md` ("Protocol daemon: per-source supervisor") is ready
  to be pruned once this lands.
