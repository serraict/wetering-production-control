# Doing: PLC Monitor v1 — discover + log

Smallest slice of [[plc_monitoring_app]] worth shipping. Goal is to **verify
the discover-and-subscribe loop works against the production Omron PLC** by
seeing real datachange events stream into a log. Everything else (TUI, Leuze,
rotation, compose service) is deferred to follow-up slices.

Full note: [`work/notes/plc_monitoring_app.md`](notes/plc_monitoring_app.md).

## Context

We have working connect / browse / write scripts against the production PLC
(`scripts/monitor_plc.py`, `scripts/write_plc.py`) using a fixed three-node
list (`ScanResultaat`, `ActievePartijnummer{1,2}`). We don't yet know whether
"subscribe to every variable the PLC exposes" is a safe and useful strategy on
this device — Leuze has known limits, the Omron should be fine, but we haven't
tried.

Until we've seen it work, the rest of the monitor design (TUI, rotation,
long-running compose service) is speculation.

## Goals

1. Discover all variables in the PLC's user namespaces at startup.
2. Subscribe to every discovered variable.
3. Emit one JSONL record per datachange to stdout.
4. Run against the **production PLC** via the `opcua_test` compose service on
   `serraserver` and observe meaningful events.

## Acceptance criteria

- [x] `uv run python -m production_control.opcua.monitor` connects to the PLC
      using `VINEAPP_OPCUA_*` env vars and the existing client cert.
      *(Verified locally against `opc_test_server.py` with
      `VINEAPP_OPCUA_SECURITY=none`; production cert/credential path is the
      same code path, unverified until the serraserver run.)*
- [x] On startup, lists every variable it discovered (one INFO line per node)
      so we can see what was found.
- [x] Subscribes to all of them; prints one JSONL line per datachange to
      stdout: `{"ts":..., "source":"plc", "node":..., "value":..., "server_ts":..., "status":...}`.
- [ ] Survives one disconnect → reconnect cycle without crashing (kill the
      network briefly, see it recover). **Deferred** — user can't test alone;
      will be done on-site with the PLC engineer.
- [x] Runs end-to-end on serraserver via
      `docker compose run --rm opcua_test python -m production_control.opcua.monitor`
      against the production PLC. Capture written to
      [`work/notes/ontstapelmachine/plc_monitor_v1_capture.md`](notes/ontstapelmachine/plc_monitor_v1_capture.md).

## Design

- New module `src/production_control/opcua/monitor.py` (single file; promote
  to a package only when it grows).
- Reuses the connection-setup pattern from `scripts/monitor_plc.py`
  (asyncua client + SignAndEncrypt + Basic256Sha256 + client cert from env).
- **Discovery:** walk children of the root `Objects` folder; for each user
  namespace (skip `ns=0` and any `http://opcfoundation.org/...`), recurse and
  collect every node whose `NodeClass == Variable`. Cap recursion depth (e.g.
  6) as a safety net.
- **Subscribe:** one subscription, one handler. Handler emits a JSONL line per
  notification using `json.dumps(..., default=str)` so timestamps and Variant
  values serialize without extra plumbing.
- **Reconnect:** on connection drop, log a WARNING, sleep 5s, re-run discovery
  + re-subscribe. No exponential backoff yet.
- No CLI flags. URL, cert paths, credentials all from env. If we need flags
  later, add them later.
- **Debug-only:** `VINEAPP_OPCUA_SECURITY=none` skips security + user auth so
  the same module can be pointed at the test server (or any anonymous
  endpoint). Production runs leave it unset.

### Explicitly out of scope for v1

- Textual TUI.
- Leuze monitoring (separate slice — different device, different constraints).
- File output / rotation / `VINEAPP_OPCUA_MONITOR_LOG_DIR`. Pipe stdout to a
  file if you want one (`... > /tmp/plc.log`).
- Long-running compose service. We run via `docker compose run --rm` until
  we've seen the logger behave for an hour or two.
- Per-node update-rate cap. If we see a chatty node, we'll add it then.
- Smoke test against `opc_test_server.py`. Verification is on the real PLC;
  the test server still has the stale `Lijn{n}/PC/OS` shape and isn't worth
  fixing inside this slice.
- Architecture doc update; operator doc.

## Implementation steps

- [x] Create `src/production_control/opcua/__init__.py` and
      `src/production_control/opcua/monitor.py`.
- [x] Extract the connection-setup boilerplate from `scripts/monitor_plc.py`
      into a small helper inside `monitor.py` (inlined `_build_client` /
      `_connect_and_run`; no import from `scripts/`).
- [x] Implement `discover_variables(root) -> list[(Node, name)]` (walks
      children of `Objects`, skips `ns=0`, caps recursion at depth 6).
- [x] Implement the subscription handler that emits JSONL (`JsonlHandler`).
- [x] Implement the reconnect loop (5s sleep, no backoff).
- [x] Run locally against `scripts/opc_test_server.py` as a sanity check —
      5 variables discovered, JSONL on initial subscribe + on `uawrite`
      datachanges.
- [x] Build and push the docker image (`make docker_push`) — done by user as
      part of the new release.
- [x] On serraserver: `docker compose pull opcua_test`, then
      `docker compose run --rm opcua_test python -m production_control.opcua.monitor`
      pointed at the production PLC. User confirmed: running and works.
- [x] Capture written to
      [`work/notes/ontstapelmachine/plc_monitor_v1_capture.md`](notes/ontstapelmachine/plc_monitor_v1_capture.md).
- [ ] Test reconnect: kill the network on serraserver briefly, confirm the
      monitor recovers. **Deferred to on-site session with PLC engineer.**
- [x] Review the capture: 9 unique variables (clean, no flood); discovery
      had a dedup bug across top-level subtrees — **fixed** in this slice;
      `AantalBollenPerKrat` ≈ deferred `bolmaat`; `Ziftmaat1/2` and `vDummy`
      are not exposed; `DeviceStatus.{Mode,ErrorStatus}` are free
      observability wins. Findings folded into
      [`work/notes/plc_monitoring_app.md`](notes/plc_monitoring_app.md).
