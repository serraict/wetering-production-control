# 2. Zulip insights bot

Date: 2026-05-27

## Status

Proposed.

## Context

Operators and the team want a low-friction way to ask ad-hoc questions
about the data the app already shows — "how many partijen are still on
the inspectie list for this week", "top 10 klanten by aantal plant
werkelijk" — without opening the app, building a view, or writing SQL
themselves.

The pieces this can lean on:

- **Dremio** already backs every overview in the app, via a SQLAlchemy
  engine over the Flight protocol (`src/production_control/data/repository.py:64`).
- The Dremio account configured at `VINEAPP_DB_CONNECTION` is already
  read-only. No new credential surface.
- The app's overviews — `potting_lots`, `bulb_picklist`, `inspectie`,
  `spacing`, `vloerplan`, `products` — are each described by a
  SQLModel class plus a `DremioRepository`. These define the curated
  set of views, columns, and example queries the team already trusts.
- Zulip is the team's existing chat backend (ADR-0001) and is the
  natural place for this conversation surface.
- The team wants to experiment with different language models, not
  commit to a single vendor.

Constraints / forces:

- Schema knowledge for the bot must not drift from the app's view of
  the world. Whatever powers the overviews should also ground the bot.
- The bot can crash, loop, or burn tokens; it must not be able to take
  the operator-facing UI or the protocol daemon down with it.
- The team wants model flexibility today, not abstraction debt to pay
  later when they realise they've over-engineered a provider layer.

## Decision

1. **Process and repo shape.** The bot lives in this repo, in a new
   package `src/production_control/bot/`, and runs as a **separate
   process** with its own compose service. It shares the codebase
   (SQLModel classes, Dremio engine, env config) but not the runtime.
   Tool-use loops are slow and bursty; they do not share an event
   loop with the web UI.

2. **Data access.** The bot writes raw `SELECT` SQL against Dremio via
   the existing `VINEAPP_DB_CONNECTION` engine. The read-only Dremio
   account is the authoritative safety boundary. A sqlglot-based
   guard adds defence in depth: single statement, `SELECT`/`WITH` only,
   `LIMIT` injected if absent, per-query statement timeout, response
   byte/row cap. No `INFORMATION_SCHEMA` exposure — the model is
   restricted to the views the app already models.

3. **Schema grounding.** At startup the bot walks the project's
   SQLModel classes and renders a system-prompt section: one block per
   overview with its Dremio view name, columns, types, and 1–2 example
   queries. Same source of truth as the app, no separate schema doc to
   maintain.

4. **Language model integration.** Calls go through **OpenRouter**
   using the OpenAI-compatible Python SDK. Model name is an env var
   (`BOT_MODEL`), defaulting to a strong tool-use model
   (e.g. `anthropic/claude-sonnet-4.6`). One module — `bot/llm.py` —
   wraps the client. No provider-interface abstraction; if direct
   Anthropic becomes desirable later for prompt-caching wins, the swap
   is a single-file change.

5. **Tool surface.** The model is given one tool in v1:
   `run_dremio_sql(query)`. Tools are organised one-file-per-tool
   under `bot/tools/`, each exporting a `SPEC` (the JSON schema sent
   to the API) and a `call(...)` implementation, collected in a tiny
   registry. SPECs are hand-written, not reflected from type hints,
   so the tool description is a first-class object. Future
   `list_overviews()` / `describe_overview(name)` tools are deferred
   until the system prompt becomes uncomfortably large.

6. **Capability.** Read-only insights for v1. No write paths, no
   actions on behalf of the user, no chart rendering. Markdown tables
   only.

7. **Conversation state.** Stateless one-shot per `@bot` mention in
   v1. Per-topic multi-turn memory is a later slice; once it lands
   it will be keyed by Zulip `(stream, topic)`, capped by turn count
   and tokens, with replies always echoing the SQL the bot ran so
   inferred context stays visible.

8. **Transport.** Zulip integration is a thin FastAPI endpoint
   wrapping a transport-agnostic `bot.answer(question) -> str`. The
   CLI entrypoint (`python -m production_control.bot.cli "..."`)
   uses the same `answer(...)`. Outgoing-webhook vs bot-user is a
   slice-2 decision; the design assumes outgoing webhook.

9. **Audit log.** Every question is appended to a JSONL audit log
   from day one — `{ts, user, topic, question, model, sql[], rows,
   latency_ms, tokens}`. Each Zulip reply carries a footer with model
   name, latency, and token usage so model experiments are visible
   to operators.

## Consequences

### Good

- **Single source of truth for schemas.** The bot can never describe
  a column the app's SQLModel classes don't already know about.
  Adding a new overview to the app automatically extends what the bot
  understands.
- **Existing safety boundary reused.** Read-only Dremio account is
  already in place; the bot doesn't add credential surface.
- **Model flexibility is cheap.** OpenRouter + `BOT_MODEL` env var
  means switching between Anthropic, OpenAI, Google, and open
  models is a config change, not a rewrite.
- **Blast radius contained.** Separate process means runaway tool
  loops, token-budget surprises, or LLM-provider outages can't take
  the operator UI or protocol daemon down.
- **Hand-written tool specs.** Tool descriptions stay legible and
  intentional rather than emerging accidentally from type hints.
- **Slim transport coupling.** `bot.answer(...)` knows nothing about
  Zulip, so CLI iteration is fast and a different transport (CLI,
  webhook, future bot-user) can be added without touching the core.

### Bad / accepted trade-offs

- **No provider-native features.** Going through OpenRouter means we
  lose direct access to features that matter to specific providers —
  e.g. Anthropic's explicit `cache_control` blocks behave differently
  across the OpenAI-compat surface, OpenAI's auto-caching is opaque,
  smaller models on the network don't cache at all. Per-call cost is
  higher than a direct-to-vendor integration would be. Accepted in
  exchange for model-experimentation velocity; revisit if cost gets
  noticeable.
- **Tool-use quality varies by model.** Claude and GPT-5-class models
  call tools reliably; smaller or open models on OpenRouter often
  invent tool args or skip the tool and hallucinate SQL results
  outright. The SQL guard catches the worst of it but answers will
  silently get worse on weaker models. Mitigated by the audit log
  and the reply footer making model identity visible.
- **Curated schema scope is a ceiling, not a floor.** Questions that
  need a join the app's SQLModel layer doesn't already perform may
  return "I don't have that data." Acceptable for v1; if it bites,
  ADR amendment to opt-in `INFORMATION_SCHEMA` access with an
  allowlist of Dremio spaces.
- **OpenRouter is a vendor in the middle.** Their outage takes the
  bot down. Mitigated by keeping `bot/llm.py` thin enough for a
  ~30-line swap to direct Anthropic/OpenAI.
- **Stateless v1 loses context across turns.** "Same query for last
  week" doesn't work without the user repeating the prior question.
  Acceptable for v1; slice 3 adds per-topic memory.
- **Schemas in the prompt cost tokens every call.** Six overviews ×
  ~20 columns is a few thousand tokens. Cached well on Anthropic
  models, less so elsewhere. Acceptable until measured otherwise.

## Future work / triggers for revisiting

- If per-call cost gets uncomfortable, switch `bot/llm.py` to direct
  Anthropic with explicit `cache_control` on the schema block, or
  introduce `list_overviews()` / `describe_overview(name)` tools so
  the system prompt can shrink.
- If users repeatedly ask follow-up questions, promote slice 3
  (per-topic memory) ahead of slice 4 polish.
- If the bot is asked to take actions ("mark this partij…", "add a
  note to…"), open a new ADR — that crosses from read-only insights
  into the app's write paths and needs its own discussion.
- If we want to limit access (per Zulip stream, per group), revisit
  decision 6/8.
