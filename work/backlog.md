# Backlog

Product increments to realize the product vision.

- **Zulip insights bot — slice 3 (per-topic memory).** Multi-turn context keyed
  by `(stream, topic)`, capped by turn count and tokens. `@bot reset` clears.
  See ADR-0002.
- **Zulip insights bot — webhook retry storms.** Observed 2026-05-29:
  Zulip's 10s webhook timeout fires while sonnet-4.6 is still thinking,
  so Zulip retries; each retry runs a full LLM+Dremio loop and gets
  persisted to topic history. One user question can become 3-5 actual
  bot calls (audit log `var/bot-audit.jsonl`, topic
  `teelt/channel events`). Two candidate fixes: (a) dedupe by Zulip
  `message.id` with a short in-memory cache so retries hit the same
  cached response; (b) switch to "ack 200 immediately, post the answer
  asynchronously via Zulip REST API" — likely subsumes the existing
  latency-triage item.
- **Zulip insights bot — ISO week computation in system prompt.** The
  prompt tells the bot how to *display* ISO week dates but not how to
  *compute* an ISO week number from a Dremio date column. Observed
  drift between `WEEK(d)`, `EXTRACT(WEEK FROM d)`, and ad-hoc YEAR
  filters in successive retries for the same question. Add a one-line
  rule: prefer `BETWEEN DATE '...' AND DATE '...'` ranges (caller
  computes the Monday/Sunday bounds), and if a derived week column is
  unavoidable, use a known-correct expression.
- **Zulip insights bot — don't persist timed-out turns in history.**
  Today every retry's `result.new_messages` is appended to
  `bot.conversation` because `result.error is None`. The topic ends
  up with N near-duplicate exchanges per real question, eroding the
  context budget fast. Likely falls out of the retry-storm fix above
  (one persisted turn per real question) but worth tracking
  separately in case that fix takes a different shape.
- **Zulip insights bot — slice 4 (polish).** Result formatting (dates, numbers,
  links back into the app), cost/latency dashboards from the audit JSONL,
  optional auth scoping. See ADR-0002.
- **Zulip insights bot — investigate latency.** Smoke-run felt slow. Instrument
  per-step timings in the audit JSONL, then triage: OpenRouter hop,
  schema-in-prompt token cost, two-round-trip pattern, or model choice. See
  `work/notes/bot/zulipbot_v1_capture.md`.
- **Zulip insights bot — graceful Dremio-unavailable.** Connection failures hang
  ~30s and the LLM may retry, blowing through Zulip's 10s webhook timeout
  (observed 2026-05-29 during slice 2 setup). Set a short Dremio connect
  timeout, distinguish "infra down" from "bad SQL" inside `run_dremio_sql`, and
  have `answer()` short-circuit on the former so the user sees a clean "Dremio
  onbereikbaar" reply.
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
- the performance of the app does not seem to be great.\
  seem if we can find a way to monitor and improve
