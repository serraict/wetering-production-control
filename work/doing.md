# Doing

See the [Working docs] for full description of the work.
Reference patterns: `docs/notes/opcua-examples/` (especially `docs/omron-connection-guide.md`).
Field-test details: `work/notes/leuze_opcua_connection.md`, `work/notes/onstapelmachine/references.md`.

## Context

- Omron PLC (production): IP/port **TBD** — to be confirmed on site.
  Protocol nodes (from test setup, expected to match): `ns=4;s=GoodRead`, `ns=4;s=Resultaat`, `ns=4;s=Trigger`.
  Credentials: to be set on the production PLC.
- Leuze DCR 202iC scanner (production): IP/port **TBD** — to be confirmed on site.
  Scan node (from test setup): `ns=5;i=6122` (LastScanData). Requires asyncua monkey-patch (see `scripts/browse_leuze.py`).
  Credentials: to be set on the production scanner.
- **Certificates must be regenerated** for the production setup — the test certs in `certs/` are not reusable. Generate with both `clientAuth` and `serverAuth` EKUs (per opcua-examples Findings); our own cert is the authentication path — no UaExpert-style workaround.
- Production control runs in a docker container on `serraserver` (10.0.0.3) under Serra Vine.
- Field tests today (2026-05-11), later this morning. Existing tests live in `work/scripts/` and were written against the test setup (Omron @ 192.168.50.36, Leuze @ 192.168.50.41) — keep as reference but rewire to the production endpoints.

## Goals (today)

1. Verify the connection to PLC and Leuze scanner with a script.
2. Monitor the protocol fields in the OS' PLC with a monitor script running on the production control container.
3. Write to the PLC using a script running on the production control container.
4. Monitor the Leuze scanner data using a script running on the production control container.
5. Write the scan result to the PLC using a script.

## Prerequisites (do first)

### A. Deploy & run check

Before field tests, prove the round-trip on serraserver: build → push → pull → run a script inside the container → see output.

- [ ] Pick a trivial canary script (e.g. `work/scripts/browse_plc.py`, retargeted to the production PLC once known)
- [ ] `make docker_push` builds and pushes `ghcr.io/serraict/wetering-production-control:latest`
- [ ] On serraserver: pull the new image and restart the container
- [ ] Exec into the container and run the canary — confirm it reaches the production PLC
- [ ] Make a one-line visible change in the canary, redeploy, confirm the new output appears

### B. Production certificates

- [ ] Confirm the production PLC + scanner IPs/ports on site
- [ ] Regenerate the client cert/key for the production deployment (CN, SAN URI, hostname all matching what the container will present); include both `clientAuth` and `serverAuth` EKUs
- [ ] Place certs where the container can read them (volume mount, not baked into the image)
- [ ] Trust the new client cert on the Omron PLC (Sysmac Studio → Client Authentication → Move to Trusted)
- [ ] Configure user accounts on the PLC and scanner; store the credentials in `.env` for the container

## Acceptance criteria

- [ ] Connection settings (URL, user, password, cert paths, app URI) read from env vars / `.env` in one place — pattern from `docs/notes/opcua-examples/client/common.py`
- [ ] Certificates and credentials accessible inside the deployed container (volume-mounted or baked in deliberately)
- [ ] Goal 1: PLC and Leuze connect scripts each print a success line from inside the container
- [ ] Goal 2: monitor logs datachange notifications for `GoodRead`, `Resultaat`, `Trigger`
- [ ] Goal 3: a write script sets a chosen PLC field; the monitor (goal 2) observes the new value
- [ ] Goal 4: monitor logs scans as they arrive from `ns=5;i=6122`
- [ ] Goal 5: combined script reads scans from Leuze and writes them to a PLC field; observed end-to-end

## Technical requirements

- `asyncua` via `uv` (already in `pyproject.toml`)
- SignAndEncrypt + Basic256Sha256 using certs in `certs/`
- Application URI ≤44 chars, matches the SAN URI in the client cert (Omron length limit)
- Leuze: monkey-patch asyncua for the malformed server certificate (see `scripts/browse_leuze.py`)
- Omron: authenticate with our own cert generated with **both** `clientAuth` and `serverAuth` EKUs (see Findings in `docs/notes/opcua-examples/docs/omron-connection-guide.md`). No UaExpert-style workaround.

## Implementation steps

- [ ] Verify deploy + run path on serraserver (prerequisite above)
- [ ] Consolidate connection config in one env-driven module mirroring `opcua-examples/client/common.py`
- [ ] Goal 1 — connect smoke tests: PLC + Leuze (reuse `work/scripts/browse_plc.py`, `scripts/browse_leuze.py`)
- [ ] Goal 2 — PLC monitor on the three protocol fields (build on `work/scripts/test_00c_plc_protocol_vars.py`)
- [ ] Goal 3 — PLC write (build on `work/scripts/write_plc_vars.py` / `test_01_write_actieve_partij.py`); verify via goal 2 monitor
- [ ] Goal 4 — Leuze monitor on `LastScanData` (build on `work/scripts/test_02_read_leuze_scan.py`)
- [ ] Goal 5 — scan-to-PLC bridge (build on `test_04_read_scan_resultaat.py` / `test_05_write_scan_resultaat.py`)
- [ ] Run each script in the container against live devices during the field test; capture output in `work/notes/onstapelmachine/`

## Notes

- Keep scripts minimal and closely aligned with `opcua-examples` patterns.
- Update `work/notes/onstapelmachine/references.md` with the confirmed production IPs, ports, and cert paths once known.

[Working docs]: https://potlilium.fibery.io/ICT_Wetering_Potlilium/Actie/Integratatie-Onstapelmachine-met-oppotproces-256?sharing-key=0b2ea7ab-9c2d-4ae1-8b2a-c016b2816fa5
