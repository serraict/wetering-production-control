# Backlog

Product increments to realize the product vision.

- **Scan-page row action on list pages.** Most list pages already render a
  view button via `create_model_view_action` in
  `web/components/model_detail_page.py`. Add a sibling `create_scan_action`
  shown next to it that navigates to the row's scan page (e.g.
  `/potting-lots/scan/{id}`, `/bulb-picklist/scan/{id}`). Wire it into the
  list pages whose rows correspond to a scannable partij/lot — at least
  potting_lots, inspectie, bulb_picklist; check spacing and uitrijden.
  QR-code rendering of the same URL is a follow-up if the line operators
  ask for it.
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
