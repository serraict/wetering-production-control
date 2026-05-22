# Ontstapelaar — Field-test status

Reference patterns: `docs/notes/opcua-examples/` (especially
`docs/omron-connection-guide.md`). Field-test details:
`work/notes/ontstapelmachine/archive/leuze_opcua_connection.md`,
`work/notes/ontstapelmachine/references.md`. Working docs: [Fibery action].

## Production endpoints (confirmed)

- Omron PLC: `opc.tcp://10.0.0.190:4840`. Protocol nodes under
  `ns=4;s=OPCScanner/fbOPC/`: `ScanResultaat`, `ActievePartijnummer1`,
  `ActievePartijnummer2`. Also exposed: `AantalBollenPerKrat` (likely the
  draft's `bolmaat`, deferred), `DeviceStatus.{Mode,ErrorStatus,
  UnpublishedVariablesStatus}`, `NumOfVars`, `NumOfValues`. `Ziftmaat1/2`
  and `vDummy` from earlier notes are **not exposed** on the production PLC
  (confirmed via discovery walk on 2026-05-21).
- Leuze DCR 202iC: `opc.tcp://10.0.0.191:4840`. Monitored nodes:
  `LastScanData` (`ns=5;i=6122`), `ScanActive` (`ns=5;i=6199`),
  `DeviceTemperature` (`ns=5;i=6116`). Malformed-cert quirk handled by
  the `LenientCertificate` patch in `src/production_control/opcua/leuze.py`
  (formerly in `scripts/browse_leuze.py` / `scripts/monitor_leuze.py`,
  both deleted).
- PLC-side access control tightened on 2026-05-12 — OPC UA user is
  restricted to the protocol nodes; writes are safe.
- Production cert in place, trusted on the Omron PLC. **365-day validity**
  — see "Hardening" below for renewal plan.

## Status

All five field-test goals from the original plan are met:

- [x] PLC + Leuze connect smoke tests (`scripts/probe_opcua_endpoint.py`
      plus the monitor module).
- [x] PLC monitor on the protocol fields — shipped as
      `src/production_control/opcua/monitor.py`. (The earlier
      `scripts/monitor_plc.py` field-test script has been removed.)
- [x] PLC write (`scripts/write_plc.py`); verified via monitor.
- [x] Leuze source: `src/production_control/opcua/leuze.py` (replaces the
      earlier `scripts/monitor_leuze.py` and `scripts/browse_leuze.py`).
- [x] Scan-to-PLC bridge — shipped as the `ontstapelaar_protocol`
      compose service (see `docs/protocol.md` for the contract and
      `docs/deployment.md` for the service definition).

Reconnect-under-load test on the PLC is still **deferred** until the next
on-site session with the PLC engineer.

## Hardening / follow-ups

- [ ] **Longer-lived client cert.** Current cert from
      `scripts/generate_client_cert.py` is valid for only 365 days
      (asyncua's `setup_self_signed_certificate` hardcodes `days=365`).
      Regenerate with multi-year validity. Likely path: call
      `asyncua.crypto.cert_gen.generate_self_signed_app_certificate(...,
      days=3650)` directly and write key + DER ourselves.
- [ ] **Cert expiry check.** Extend `scripts/show_opcua_config.py` (or a
      new script) to report `notBefore` / `notAfter` for
      `VINEAPP_OPCUA_CLIENT_CERT` and warn when expiry is within N days.
      Wire into a serraserver routine (cron, healthcheck, or oncall
      checklist).
- [ ] **Runbook: cert renewal.** Document the renew + re-trust procedure
      here: regenerate via the `opcua_test` service into the certs volume,
      re-trust on the Omron PLC (Sysmac Studio → Client Authentication),
      restart `production_control`, verify with the monitor.

## Open questions for the PLC engineer

Promoted from the v1/v2 monitor captures (now deleted) so they survive
until the next on-site session.

- Is `DeviceStatus.ErrorStatus == "ContinuousError"` the steady-state
  value, or a real fault?
- Confirm: `AantalBollenPerKrat` is the PLC's existing slot for what
  the draft calls `bolmaat` — i.e. when we wire bolmaat, we write to
  that variable rather than create a new one?
- What does `UnpublishedVariablesStatus` actually count? Useful as a
  monitor signal or noise?

## Commands

Operator commands live in
[`docs/deployment.md`](../../../docs/deployment.md) under "Running on
serraserver".

[Fibery action]:
  https://potlilium.fibery.io/ICT_Wetering_Potlilium/Actie/Integratatie-Onstapelmachine-met-oppotproces-256?sharing-key=0b2ea7ab-9c2d-4ae1-8b2a-c016b2816fa5
