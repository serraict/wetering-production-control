# Zulip insights bot — v2 (slice 2) capture

Shipped: `c6257b4` (2026-05-29). Slice 2 of ADR-0002 — Zulip
outgoing-webhook FastAPI transport.

## What worked end-to-end

- @-mention in `#teelt` → bot answered in Dutch with a markdown table
  and footer. Mention stripping handled the `@**serradata**` prefix
  cleanly. Stream/topic routing was automatic — Zulip posts the reply
  in the same topic.
- 7.97s observed latency on a 3-week aggregation (sonnet-4.6, 2 tool
  iterations, 6937 tokens). Comfortably under Zulip's 10s webhook
  timeout *when Dremio responds*.
- Compose service `bot:` is wired and ready for prod deployment via
  Traefik; mirrors the existing web service's setup.
- Import-graph hygiene held: `bot.answer` still doesn't pull in
  FastAPI; `bot.server` doesn't pull in the zulip package.

## What surprised us (Zulip-side setup)

- **Outgoing-webhook `token` ≠ bot API key.** The card in
  Settings → Personal → Bots shows an "API KEY" field, but Zulip
  sends a *different* value (`Service.token`) as the JSON `token`
  on every webhook POST. The right value lives in the
  `.zuliprc` bundled by the "Download config of all active outgoing
  webhook bots" link. Cost ~30 min of 401 troubleshooting.
  Documented in `.env.example`.
- **`host.docker.internal:7902` works from Zulip → host.** The
  Docker bridge gateway IP (`192.168.160.1` on serra-vine) does
  *not* — it's an internal route, not the macOS host. Two earlier
  attempts at the gateway IP gave "Failed to connect to remote host"
  (502 from Zulip).
- **The Zulip bot-creation form pre-rejects some URLs as invalid.**
  Paste hygiene (no leading spaces, no surrounding quotes) matters.
  Once the bot exists the URL can be edited under "Configure".

## What surprised us (bot behaviour)

- **Dremio unavailable → Zulip "bot unavailable".** When Dremio is
  down, the SQLAlchemy connect hangs ~30s and the LLM may retry,
  blowing through Zulip's 10s webhook timeout. The bot's `answer()`
  already turns tool errors into LLM-visible `"ERROR: ..."` text, but
  there's no fail-fast on infra outage. Backlogged: graceful
  Dremio-unavailable handling.

## What we left in (deliberately) for future debugging

- Token mismatch + bot-name fingerprint logging was very useful while
  diagnosing the wrong-token issue and ultimately revealed
  `Service.token`. We reverted it before commit; the helper pattern
  is worth re-introducing temporarily during similar future setup.

## Deferred to later slices

- **Per-topic memory** (slice 3): keying conversation by
  `(stream, topic)`, `@bot reset`.
- **Polish** (slice 4): result formatting (locale-aware numbers/dates,
  links back into the app), cost/latency dashboards from the audit
  JSONL, optional auth scoping.
- **Graceful Dremio-unavailable** (own backlog item, see above).
- **Latency triage** (still on backlog): 7.97s on a simple aggregate
  is borderline for Zulip; an "ack now, answer later" pattern via
  Zulip's REST API may eventually be needed.
