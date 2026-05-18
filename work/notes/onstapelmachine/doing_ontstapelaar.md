# Doing

See the [Working docs] for full description of the work. Reference patterns:
`docs/notes/opcua-examples/` (especially `docs/omron-connection-guide.md`).
Field-test details: `work/notes/leuze_opcua_connection.md`,
`work/notes/onstapelmachine/references.md`.

## Context

- Omron PLC (production): `opc.tcp://10.0.0.190:4840`. Protocol nodes (under
  `ns=4;s=OPCScanner/fbOPC/`): `ScanResultaat`, `ActievePartijnummer1`,
  `ActievePartijnummer2`, `Ziftmaat1`, `Ziftmaat2`, `vDummy`. (Names may change
  as the PLC program evolves.) Client cert trusted on the PLC; reads work;
  writes work via `scripts/write_plc.py`. PLC-side access control was tightened
  on 2026-05-12 — the OPC UA user is restricted to the protocol nodes, so writes
  are now safe.
- Leuze DCR 202iC scanner (production): `opc.tcp://10.0.0.191:4840`. Monitored
  nodes: `LastScanData` (`ns=5;i=6122`), `ScanActive` (`ns=5;i=6199`),
  `DeviceTemperature` (`ns=5;i=6116`). Same malformed-cert quirk as the test
  unit — monkey-patch in `scripts/monitor_leuze.py` / `scripts/browse_leuze.py`.
- **Certificates must be regenerated** for the production setup — the test certs
  in `certs/` are not reusable. Generate with both `clientAuth` and `serverAuth`
  EKUs (per opcua-examples Findings); our own cert is the authentication path —
  no UaExpert-style workaround.
- Production control runs in a docker container on `serraserver` (10.0.0.3)
  under Serra Vine.
- Field tests today (2026-05-11), later this morning. Existing tests live in
  `work/scripts/` and were written against the test setup (Omron @
  192.168.50.36, Leuze @ 192.168.50.41) — keep as reference but rewire to the
  production endpoints.

## Goals (today)

1. Verify the connection to PLC and Leuze scanner with a script.
2. Monitor the protocol fields in the OS' PLC with a monitor script running on
   the production control container.
3. Write to the PLC using a script running on the production control container.
4. Monitor the Leuze scanner data using a script running on the production
   control container.
5. Write the scan result to the PLC using a script.

## Prerequisites (do first)

### A. Deploy & run check

Before field tests, prove the round-trip on serraserver: build → push → pull →
run a script inside the container → see output.

- [x] Pick a trivial canary script (e.g. `work/scripts/browse_plc.py`,
      retargeted to the production PLC once known)
- [x] `make docker_push` builds and pushes
      `ghcr.io/serraict/wetering-production-control:latest`
- [x] On serraserver: pull the new image and restart the container
- [x] Exec into the container and run the canary — confirm it reaches the
      production PLC
- [x] Make a one-line visible change in the canary, redeploy, confirm the new
      output appears

### B. Production certificates

- [x] Confirm the production PLC + scanner IPs/ports on site
- [x] Add the `opcua_test` sibling service to `docker-compose.yml` on
      serraserver (image, env_file, certs volume — see "Commands to run on
      serraserver" below)
- [x] Regenerate the client cert/key for the production deployment via the
      `opcua_test` service (CN, SAN URI, hostname all matching what the
      container will present); include both `clientAuth` and `serverAuth` EKUs
- [x] Place certs where the container can read them (volume mount, not baked
      into the image)
- [x] Trust the new client cert on the Omron PLC (Sysmac Studio → Client
      Authentication → Move to Trusted)
- [x] Configure user accounts on the PLC and scanner; store the credentials in
      `.env` for the container
- [x] **Tighten PLC access control** — done on PLC side 2026-05-12; OPC UA user
      is restricted to the protocol nodes

## Acceptance criteria

- [x] Connection settings (URL, user, password, cert paths, app URI) read from
      env vars / `.env` in one place — pattern from
      `docs/notes/opcua-examples/client/common.py`
- [x] Certificates and credentials accessible inside the deployed container
      (volume-mounted or baked in deliberately)
- [x] Goal 1: PLC and Leuze connect scripts each print a success line from
      inside the container
- [x] Goal 2: monitor logs datachange notifications for `GoodRead`, `Resultaat`,
      `Trigger` (`scripts/monitor_plc.py`)
- [x] Goal 3: a write script sets a chosen PLC field; the monitor (goal 2)
      observes the new value (`scripts/write_plc.py`)
- [x] Goal 4: monitor logs scans as they arrive from `ns=5;i=6122`
      (`scripts/monitor_leuze.py`)
- [ ] Goal 5: combined script reads scans from Leuze and writes them to a PLC
      field; observed end-to-end

## Technical requirements

- `asyncua` via `uv` (already in `pyproject.toml`)
- SignAndEncrypt + Basic256Sha256 using certs in `certs/`
- Application URI ≤44 chars, matches the SAN URI in the client cert (Omron
  length limit)
- Leuze: monkey-patch asyncua for the malformed server certificate (see
  `scripts/browse_leuze.py`)
- Omron: authenticate with our own cert generated with **both** `clientAuth` and
  `serverAuth` EKUs (see Findings in
  `docs/notes/opcua-examples/docs/omron-connection-guide.md`). No UaExpert-style
  workaround.

## Implementation steps

- [x] Verify deploy + run path on serraserver
- [x] Consolidate connection config — all scripts read `VINEAPP_OPCUA_*` env
      vars
- [x] Goal 1 — PLC + Leuze connect smoke tests
      (`scripts/probe_opcua_endpoint.py`, `scripts/monitor_plc.py`,
      `scripts/monitor_leuze.py`)
- [x] Goal 2 — PLC monitor on the three protocol fields
      (`scripts/monitor_plc.py`)
- [x] Goal 4 — Leuze monitor (`scripts/monitor_leuze.py`)
- [x] **PLC access control:** OPC UA user restricted to the protocol nodes (done
      on PLC side 2026-05-12)
- [x] Goal 3 — PLC write script (`scripts/write_plc.py`); verify via goal 2
      monitor
- [ ] Goal 5 — scan-to-PLC bridge (build on `test_04_read_scan_resultaat.py` /
      `test_05_write_scan_resultaat.py`)
- [ ] Capture field-test output in `work/notes/onstapelmachine/`

## Hardening / follow-ups

- [ ] **Longer-lived client cert.** Current cert generated by
      `scripts/generate_client_cert.py` is valid for only 365 days (asyncua's
      `setup_self_signed_certificate` hardcodes `days=365`). Regenerate with a
      multi-year validity (e.g., 10 years) so we don't get surprised by an
      expiry. Likely path: stop using the convenience helper and call
      `asyncua.crypto.cert_gen.generate_self_signed_app_certificate(..., days=3650)`
      directly, then write key + DER cert ourselves.
- [ ] **Cert expiry check.** Add a script (or extend
      `scripts/show_opcua_config.py`) that reports `notBefore` / `notAfter` for
      `VINEAPP_OPCUA_CLIENT_CERT` and warns when expiry is within N days. Wire
      it into a routine on serraserver (cron, healthcheck, or oncall checklist).
- [ ] **Runbook: cert renewal.** Document in `work/notes/onstapelmachine/` what
      to do when the cert expires (or is about to): regenerate via the
      `opcua_test` service into `production-control/certs/`, re-trust the new
      cert on the Omron PLC (Sysmac Studio → Client Authentication), restart
      `production_control`, verify with `monitor_plc.py` / `monitor_leuze.py`.

## Notes

- Keep scripts minimal and closely aligned with `opcua-examples` patterns.
- Update `work/notes/onstapelmachine/references.md` with the confirmed
  production IPs, ports, and cert paths once known.

### Commands to run on serraserver

```sh
# update
docker compose pull opcua_test
```

Then, from the deployment dir:

```sh
docker compose run --rm opcua_test python scripts/show_opcua_config.py

# generate the client cert into the shared certs volume
docker compose run --rm opcua_test \
  python scripts/generate_client_cert.py --out-dir /app/certs --hostname "$(hostname)"

# probe both endpoints (URLs come from the container's env_file)
docker compose run --rm opcua_test sh -c \
  'python scripts/probe_opcua_endpoint.py "$VINEAPP_OPCUA_PLC_URL"'
docker compose run --rm opcua_test sh -c \
  'python scripts/probe_opcua_endpoint.py "$VINEAPP_OPCUA_LEUZE_URL"'

# monitor PLC protocol fields (GoodRead / Resultaat / Trigger)
docker compose run --rm opcua_test python scripts/monitor_plc.py

# monitor Leuze scanner variables
docker compose run --rm opcua_test python scripts/monitor_leuze.py

# write PLC protocol variables (see --help for all flags)
docker compose run --rm opcua_test python scripts/write_plc.py --scanresultaat 27246
docker compose run --rm opcua_test python scripts/write_plc.py --clear

# once the cert is trusted on the PLC
docker compose up -d production_control
```

[Working docs]:
  https://potlilium.fibery.io/ICT_Wetering_Potlilium/Actie/Integratatie-Onstapelmachine-met-oppotproces-256?sharing-key=0b2ea7ab-9c2d-4ae1-8b2a-c016b2816fa5
