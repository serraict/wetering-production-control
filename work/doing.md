# Doing

## Context

The `ontstapelaar_protocol` container holds two long-lived OPC/UA
subscriptions (PLC + Leuze, each wrapped in `supervise(..., max_attempts=None)`
in `src/production_control/opcua/protocol/scan_cycle.py`). When a device
goes unreachable today, the supervisor logs reconnect attempts but
nothing surfaces outside the container — there is no signal Prometheus
can scrape.

Prometheus is already running elsewhere in the stack. The cheapest way
to feed it a per-device up/down signal is a Docker `HEALTHCHECK` on the
`ontstapelaar_protocol` service, exposed to Prometheus via whatever
container-state exporter is already wired up.

A naïve healthcheck that opens its own OPC session every 30s would
double-connect against the Omron (and the Leuze, which is already
fragile around session limits — see [[opcua_test_compose_service_pattern]]
and the LenientCertificate notes in MEMORY.md). Instead: the daemon
writes a heartbeat file per role while its subscription is live; the
healthcheck reads `mtime`.

## Goals

A Docker `HEALTHCHECK` on `ontstapelaar_protocol` that reports
`unhealthy` when either the PLC or Leuze subscription has been down for
more than a configurable threshold. No second OPC session opened by
the check itself.

## Acceptance criteria

- [x] Each supervised loop in `protocol/scan_cycle.py` touches a
      per-role heartbeat file (`/tmp/opcua-plc.alive`,
      `/tmp/opcua-leuze.alive`) every ~10s while its subscription is
      live, and stops touching it on disconnect / shutdown.
- [x] New `src/production_control/opcua/healthcheck.py` exits 0 when
      both heartbeat files exist and `mtime` is within the freshness
      threshold; exits non-zero otherwise. Prints which device is
      stale on stderr so `docker inspect` shows the reason.
- [x] `HEALTHCHECK` block added to the `ontstapelaar_protocol` service
      in `docker-compose.yml`. Not added to `Dockerfile` — the image's
      default entrypoint runs the web app, not the protocol daemon,
      so a Dockerfile-level HEALTHCHECK would be misleading on `docker
      run` of the same image.
- [x] Unit tests in `tests/opcua/test_healthcheck.py` cover: both
      fresh → exit 0; one stale → exit non-zero with the role named;
      missing file → exit non-zero. Use a tmp_path-based heartbeat
      directory injected via env var so the test doesn't touch
      `/tmp`.
- [x] `make quality` green.

## Design

### Heartbeat write

- New `src/production_control/opcua/heartbeat.py` with a tiny helper:
  ```python
  HEARTBEAT_DIR = os.environ.get("VINEAPP_OPCUA_HEARTBEAT_DIR", "/tmp")
  HEARTBEAT_INTERVAL_S = 10

  def path_for(role: str) -> Path:
      return Path(HEARTBEAT_DIR) / f"opcua-{role}.alive"

  async def beat_while_alive(role: str, stop_event: asyncio.Event) -> None:
      """Touch the role's heartbeat file every HEARTBEAT_INTERVAL_S
      seconds until stop_event fires."""
  ```
- In `protocol/scan_cycle.py::_plc_loop` and `_leuze_loop`, replace
  `await stop_event.wait()` with `asyncio.gather(beat_while_alive(role, stop_event), stop_event.wait())`
  (or run the beat as a task alongside the existing wait). The
  heartbeat starts only after `ready.set()` so we don't flap a green
  signal during the initial connect.
- On supervised disconnect / exception, the beat task is cancelled and
  the file goes stale on its own. No explicit "delete file on error"
  step — simpler, and naturally captures "process alive but
  reconnecting" as `unhealthy`.

### Healthcheck script

- `python -m production_control.opcua.healthcheck`. ~30 lines.
- Reads `HEARTBEAT_DIR` and a `VINEAPP_OPCUA_HEARTBEAT_MAX_AGE_S`
  (default 30s — 3× interval, gives one missed beat of slack).
- For each role in `("plc", "leuze")`: check the file exists and
  `time.time() - mtime < max_age`. Collect failures, print
  `unhealthy: plc stale (last beat 47s ago)` on stderr, exit 1.
- Reuses the same env var for the dir so docker-compose only sets it
  once.

### docker-compose wiring

```yaml
ontstapelaar_protocol:
  ...
  healthcheck:
    test: ["CMD", "python", "-m", "production_control.opcua.healthcheck"]
    interval: 30s
    timeout: 5s
    retries: 2
    start_period: 60s
```

`start_period` is generous because the secure-mode handshake against
the real Leuze (with LenientCertificate kicking in) can take a few
seconds, plus reconnect backoff if the first connect fails.

### Prometheus side (out of this slice)

Whatever already scrapes Docker (cadvisor / docker-state-exporter)
will pick up `container_health_status` automatically. Confirm with
the user which exporter exists before we add any dashboard /
alerting rules — that's the next slice if we want one.

## Implementation steps

- [x] Add `opcua/heartbeat.py` with `path_for` + `beat_while_alive`
      and unit tests.
- [x] Wire `beat_while_alive("plc", stop_event)` into `_plc_loop`
      after `ready.set()`; same for leuze. Cleanup in `finally`
      cancels the beat task and awaits it before sub.delete().
- [x] Add `opcua/healthcheck.py` + `tests/opcua/test_healthcheck.py`.
- [x] Add `HEALTHCHECK` to `ontstapelaar_protocol` in
      `docker-compose.yml`. Compose-only (see acceptance criteria
      note).
- [x] `make quality`.
- [ ] Manual verify against the test setup: bring up the daemon,
      `docker inspect --format '{{.State.Health.Status}}'
      wetering-production-control_ontstapelaar_protocol_1` reports
      `healthy`; kill the Leuze container (or block the IP)
      and watch it flip to `unhealthy` within ~60s. **← user to do.**

## Open questions

- Which container-state exporter is feeding Prometheus today
  (cadvisor / docker-state-exporter / something else)? Determines
  the metric name to alert on but doesn't block this slice.
- Should the heartbeat threshold be tighter (e.g. 20s) so a single
  missed reconnect attempt counts as unhealthy? Default 30s is
  forgiving; can tune after we see real reconnect timing in prod.
