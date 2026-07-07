# Leuze scanner — production connect & test plan

Date: 2026-07-07. Goal: connect the production Leuze DCR 202iC to
Production Control and verify the scan path end-to-end.

## What's already in place (code review)

- **Client code is ready.** `src/production_control/opcua/leuze.py`
  subscribes to a fixed 3-node set (`LastScanData` ns=5;i=6122,
  `ScanActive` ns=5;i=6199, `DeviceTemperature` ns=5;i=6116). Full-tree
  browse is intentionally avoided (`BadEncodingLimitsExceeded` on
  firmware V2.4.0).
- **Malformed server cert handled.** The `LenientCertificate`
  monkey-patch is applied on import of `leuze.py`; confirmed needed on
  the production unit too (same firmware). Expect the log line
  "Using lenient certificate parser for malformed server cert" — that's
  normal, not an error.
- **Config contract** (`opcua/config.py`): secure mode needs
  `VINEAPP_OPCUA_LEUZE_URL`, `VINEAPP_OPCUA_LEUZE_USER`,
  `VINEAPP_OPCUA_LEUZE_PASSWORD`, plus the shared
  `VINEAPP_OPCUA_CLIENT_CERT` / `VINEAPP_OPCUA_CLIENT_KEY`.
  Security: Basic256Sha256 + SignAndEncrypt, user/password auth.
- **Graceful absence.** With `VINEAPP_OPCUA_LEUZE_URL` unset, the
  monitor, TUI, and protocol daemon all skip the Leuze source — so we
  can stage the env vars one at a time without breaking the PLC side.
- **Supervision.** The protocol daemon supervises PLC and Leuze
  independently (a Leuze outage can't kill the PLC loop) and each role
  feeds the Docker healthcheck heartbeat.
- **Same client cert for both servers.** PC presents one Application
  Instance cert to the PLC and the Leuze. If the PLC connection already
  works in production, the cert exists in the certs volume — reuse it,
  don't regenerate (regenerating would break PLC trust).

## Open items to resolve on-site (before testing)

1. **Production IP / URL.** Docs assume `opc.tcp://10.0.0.191:4840` —
   confirm the actual address and that serraserver (10.0.0.3) can route
   to it.
2. **User account on the scanner.** Test bench used `Martin` /
   `12345678` (capital M — the scanner is case-sensitive). Production
   needs its own account, configured via the Leuze web interface /
   Sensor Studio. Store the credentials in `.env` on serraserver only.
3. **Client cert trust on the scanner.** Check whether the Leuze needs
   our client cert in its trust list or accepts any cert with valid
   user credentials. (This wasn't captured from the test-bench setup —
   note what you find.)
4. **Node IDs.** Verify `ns=5;i=6122` (LastScanData) exists on the
   production unit; numeric ids can shift between firmware builds. Use
   `monitor list --target leuze` (step 3 below) — it reads exactly the
   fixed node set.

## Test ladder

Run from the deployment directory on serraserver. Each step only
depends on the previous one passing; stop and triage at the first
failure.

### 0. Prep

- Add `VINEAPP_OPCUA_LEUZE_URL`, `_USER`, `_PASSWORD` to `.env`.
- `docker compose pull opcua_test` (make sure image is current).

### 1. Env sanity

```sh
docker compose run --rm opcua_test python scripts/opc/show_config.py
```

Expect: all Leuze vars reported set, cert/key paths resolve.

### 2. Reachability + endpoint discovery (no auth needed)

```sh
docker compose run --rm opcua_test sh -c \
  'python scripts/opc/probe_endpoint.py "$VINEAPP_OPCUA_LEUZE_URL"'
```

Expect: endpoint list including policy `Basic256Sha256`, mode
`SignAndEncrypt`, and the scanner's application URI.

- FAIL/timeout → network/routing problem, not OPC. Check IP, VLAN,
  firewall between serra-vine network and the plant network.

### 3. Authenticated read of the fixed nodes

```sh
docker compose run --rm opcua_test \
  python -m production_control.opcua.monitor list --target leuze
```

First real handshake: lenient-cert patch + client cert + user/pwd.
Expect: current values for LastScanData, ScanActive,
DeviceTemperature.

- `BadSecurityChecksFailed` → scanner doesn't trust our client cert
  (see open item 3).
- `BadUserAccessDenied` / `BadIdentityTokenRejected` → credentials
  (check case-sensitivity).
- Node read errors with connection OK → node-id mismatch (open item 4).

### 4. Subscription (streaming monitor)

```sh
docker compose run --rm opcua_test python -m production_control.opcua.monitor
```

Expect: JSONL events on stdout; DeviceTemperature gives a slow
heartbeat, ScanActive toggles when the scanner triggers.

### 5. Physical scan

With the monitor from step 4 running, scan a krat label (or a printed
test label). Expect a `LastScanData` event whose value is the scan URL,
e.g. `https://pc.potlilium.serraict.me/potting-lots/scan/27246` —
partij id is the last path segment.

### 6. End-to-end protocol (only if the PLC is also connected)

```sh
docker compose up -d ontstapelaar_protocol
docker compose logs -f ontstapelaar_protocol
```

- Set an active partij in the web UI.
- Scan a krat of that partij.
- Verify in the logs: guard sees `last_scan_data == 0`, PC writes
  `AantalBollenPerKrat` then `ScanResultaat`, OS resets to 0 after
  pickup, vrijgave happens on the machine.
- Also try a krat of a *non*-active partij: scan is acked to the PLC
  the same way, but OS must refuse vrijgave.

### 7. Capture

Note findings (surprises, wrong assumptions, deferred items) in
`work/notes/ontstapelaar/leuze_connect_capture.md`. Update
`docs/protocol.md` / `docs/deployment.md` if the production URL or any
node id differs from what's documented. Credentials stay in `.env`,
never in the repo.

## Reference

- Test-bench facts (IPs, creds, quirks): agent memory `MEMORY.md`
  (Ontsapelaar OPC/UA Connections). Test setup was 192.168.50.41,
  user `Martin`.
- Deployment/cert details: `docs/deployment.md`.
- Protocol contract: `docs/protocol.md`.
