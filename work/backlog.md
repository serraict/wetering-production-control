# Backlog

Product increments to realize the product vision.

- **PLC reconnect-under-load test.** Deferred until next on-site session with
  the PLC engineer.
- **Cert expiry warning.** Extend `scripts/opc/show_config.py` (or new script)
  to report `notBefore` / `notAfter` for `VINEAPP_OPCUA_CLIENT_CERT` and warn
  within N days. Wire into a serraserver cron/healthcheck.
- **Runbook: client-cert renewal.** Document regenerate-via-`opcua_test` →
  re-trust on Omron PLC (Sysmac Studio → Client Authentication) → restart
  `production_control` → verify with monitor.
- **PLC engineer Q's (next on-site).** (1) Is
  `DeviceStatus.ErrorStatus == "ContinuousError"` steady-state or a real fault?
  (2) What does `UnpublishedVariablesStatus` count — useful signal or noise?
- **`aantal_bollen_per_krat` real source.** PC currently writes a constant `600`
  via a single function. Replace with a lookup from the bollen-picklist for the
  scanned partij. Verify the lookup path first (which table/field).
- the performance of the app does not seem to be great.\
  seem if we can find a way to monitor and improve
- **Zulip insights bot — current date in system prompt.** v1 used 2025
  for "this year" filters because the model has no temporal anchor.
  Inject today's date into the system prompt. Tiny fix; do before
  slice 2. See `work/notes/bot/zulipbot_v1_capture.md`.
- **Zulip insights bot — slice 2 (Zulip transport).** Add a FastAPI
  `/zulip` outgoing-webhook endpoint wrapping `bot.answer(...)`. New
  compose service. See ADR-0002.
- **Zulip insights bot — slice 3 (per-topic memory).** Multi-turn
  context keyed by `(stream, topic)`, capped by turn count and tokens.
  `@bot reset` clears. See ADR-0002.
- **Zulip insights bot — slice 4 (polish).** Result formatting (dates,
  numbers, links back into the app), cost/latency dashboards from the
  audit JSONL, optional auth scoping. See ADR-0002.
- **Zulip insights bot — investigate latency.** Smoke-run felt slow.
  Instrument per-step timings in the audit JSONL, then triage:
  OpenRouter hop, schema-in-prompt token cost, two-round-trip pattern,
  or model choice. See `work/notes/bot/zulipbot_v1_capture.md`.
