# Backlog

Product increments to realize the product vision.

- **Protocol daemon: per-source supervisor.** Today `protocol/scan_cycle.py`
  has no `supervise()` wrapper, so any failure in `_leuze_loop` (e.g. Leuze
  unreachable, asyncua `set_security` timing out during its endpoint probe)
  kills `_plc_loop` via `asyncio.gather` and the container crash-loops. Wrap
  each role's loop in `supervise()` (already in `monitor.py`) and drop the
  `RECONNECT_MAX_ATTEMPTS` giveup for the protocol daemon — Docker's
  `restart: unless-stopped` is the right policy for "process truly broken";
  the supervisor's job is riding out transient outages. Add a unit test that
  asserts a Leuze failure doesn't kill the PLC loop.
- Show scan details page from the potting list and inspection list so the scan
  screen is one click away for commenting.
- Show QR code button on the potting list.
- **PLC reconnect-under-load test.** Deferred until next on-site session with
  the PLC engineer.
- **Longer-lived client cert.** `scripts/opc/generate_client_cert.py` uses asyncua's
  `setup_self_signed_certificate` (hardcoded 365 days). Switch to
  `generate_self_signed_app_certificate(..., days=3650)` and write key + DER
  ourselves.
- **Cert expiry warning.** Extend `scripts/opc/show_config.py` (or new
  script) to report `notBefore` / `notAfter` for `VINEAPP_OPCUA_CLIENT_CERT`
  and warn within N days. Wire into a serraserver cron/healthcheck.
- **Runbook: client-cert renewal.** Document regenerate-via-`opcua_test` →
  re-trust on Omron PLC (Sysmac Studio → Client Authentication) → restart
  `production_control` → verify with monitor.
- **PLC engineer Q's (next on-site).** (1) Is
  `DeviceStatus.ErrorStatus == "ContinuousError"` steady-state or a real
  fault? (2) Confirm `AantalBollenPerKrat` is the slot for `bolmaat` (write
  there, don't add a variable). (3) What does `UnpublishedVariablesStatus`
  count — useful signal or noise?
